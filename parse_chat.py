#!/usr/bin/env python3
import json
import sys
from datetime import datetime
from collections import defaultdict
import argparse
import os

def parse_timestamp(ts_data):
    """Handle $date $numberLong format."""
    if isinstance(ts_data, dict) and '$date' in ts_data and '$numberLong' in ts_data['$date']:
        ms = int(ts_data['$date']['$numberLong'])
        if ms == 0:
            return datetime(1970, 1, 1)
        return datetime.fromtimestamp(ms / 1000)
    raise ValueError(f"Invalid timestamp: {ts_data}")

def main(json_file, output_file=None, date_end=None, convo_title=None, chunk_size=2000):
    print(f"Loading {json_file}...", file=sys.stderr)
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"JSON loaded. Conversations array length: {len(data.get('conversations', []))}", file=sys.stderr)

    responses = []
    matching_convo = None
    for i, conv in enumerate(data.get('conversations', [])):
        title = conv.get('conversation', {}).get('title', 'Untitled')
        if convo_title and convo_title not in title:
            continue
        print(f"Processing convo {i+1} (title: {title})", file=sys.stderr)
        matching_convo = conv
        resp_list = conv.get('responses', [])
        print(f"  Found {len(resp_list)} raw responses", file=sys.stderr)
        for j, resp in enumerate(resp_list):
            r = resp['response']
            try:
                ts = parse_timestamp(r['create_time'])
                cleaned_msg = r['message'].strip()
                responses.append({
                    'id': r['_id'],
                    'ts': ts,
                    'sender': r['sender'],
                    'message': cleaned_msg,
                    'parent_id': r.get('parent_response_id'),
                    'media': r.get('media_types', [])
                })
                if j < 5:
                    print(f"  Added response {j+1}: {r['sender']} len={len(cleaned_msg)} ts={ts}", file=sys.stderr)
                elif j % 100 == 0:
                    print(f"  Added response {j+1}: ... (total so far {len(responses)})", file=sys.stderr)
            except (KeyError, ValueError) as e:
                print(f"  Skipping response {j+1}: {e}", file=sys.stderr)
                continue
        break

    if not matching_convo:
        print(f"ERROR: No convo matching title '{convo_title}'. Available titles:", file=sys.stderr)
        for conv in data['conversations'][:10]:
            print(f"  - {conv.get('conversation', {}).get('title', 'Untitled')}", file=sys.stderr)
        return

    print(f"Total loaded responses: {len(responses)}", file=sys.stderr)

    if date_end:
        end_dt = datetime.strptime(date_end, '%Y-%m-%d')
        responses = [r for r in responses if r['ts'].date() <= end_dt.date()]
        print(f"Filtered to {len(responses)} responses up to {date_end}", file=sys.stderr)

    if not responses:
        print("ERROR: No responses loaded. Check timestamps or structure.", file=sys.stderr)
        return

    children = defaultdict(list)
    for resp in responses:
        if resp['parent_id']:
            children[resp['parent_id']].append(resp['id'])

    print(f"Built tree with {sum(len(kids) for kids in children.values())} branches", file=sys.stderr)

    sys.setrecursionlimit(20000)
    print("Set recursion limit to 20000", file=sys.stderr)

    memo = {}
    def subtree_size(node_id):
        if node_id in memo:
            return memo[node_id]
        size = 1
        for child_id in children.get(node_id, []):
            size += subtree_size(child_id)
        memo[node_id] = size
        return size

    for resp in responses:
        subtree_size(resp['id'])

    responses.sort(key=lambda x: x['ts'])

    output_lines = []
    for resp in responses:
        sender_pad = resp['sender'].upper().ljust(10)
        media_note = f" [Audio]" if 'audio' in resp['media'] else ""
        line = f"[{resp['ts'].strftime('%Y-%m-%d %H:%M:%S')}]{media_note} {sender_pad}: {resp['message']}"
        
        branches = children.get(resp['id'], [])
        if len(branches) >= 2:
            line += f" [ Branches: {len(branches)}]"
            for i, child_id in enumerate(branches, 1):
                child_resp = next(r for r in responses if r['id'] == child_id)
                line += f"\n* Branch {i}: [{child_resp['ts'].strftime('%Y-%m-%d %H:%M:%S')}] MSGS: {subtree_size(child_id)}"
        
        output_lines.append(line)

    # Auto-chunking with continuity markers
    total_chunks = (len(output_lines) + chunk_size - 1) // chunk_size
    for i in range(0, len(output_lines), chunk_size):
        chunk_lines = output_lines[i:i + chunk_size]
        start_ts = responses[i]['ts'].strftime('%Y-%m-%d %H:%M:%S') if i < len(responses) else "End"
        end_ts = responses[min(i + chunk_size - 1, len(responses) - 1)]['ts'].strftime('%Y-%m-%d %H:%M:%S') if chunk_lines else "End"
        chunk_num = i // chunk_size + 1
        
        header = f"[Chunk {chunk_num}/{total_chunks}: Starts {start_ts}, Ends {end_ts}]\n"
        footer = f"\n[Chunk {chunk_num}/{total_chunks} Ends: {end_ts}]"
        
        chunk_content = header + '\n'.join(chunk_lines) + footer
        
        if output_file:
            chunk_file = f"ani_chunk_{chunk_num:03d}.txt" if not os.path.splitext(output_file)[1] else f"{os.path.splitext(output_file)[0]}_{chunk_num:03d}{os.path.splitext(output_file)[1]}"
            with open(chunk_file, 'w', encoding='utf-8') as out:
                out.write(chunk_content + '\n')
            print(f"Written: {chunk_file} ({len(chunk_lines)} lines)", file=sys.stderr)
        else:
            sys.stdout.buffer.write(chunk_content.encode('utf-8') + b'\n')

    print(f"Output written: {len(output_lines)} lines across {total_chunks} chunks", file=sys.stderr)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse Grok JSON to readable chat TXT with auto-chunking')
    parser.add_argument('json_file', help='Path to JSON file')
    parser.add_argument('-o', '--output', help='Base output file (e.g., main.txt, will split to chunks numbered main_001.txt etc.)')
    parser.add_argument('--date-end', help='End date for chunk (YYYY-MM-DD)')
    parser.add_argument('--convo-title', help='Process only convo with this title substring (e.g., "Troubleshooting")')
    parser.add_argument('--chunk-size', type=int, default=2000, help='Lines per chunk (default: 2000)')
    args = parser.parse_args()
    main(args.json_file, args.output, args.date_end, args.convo_title, args.chunk_size)
