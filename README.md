# xAIBackupParser

Takes the prod-grok-backed.json file from your xAI backup and extracts a conversation into a text file.

## Features
- Extracts responses from a specific conversation (default: "Troubleshooting Interactive Mode Challenges").
- Handles timestamps and media notes (e.g., [Audio]).
- Supports filtering by date end.
- Chunks large outputs into manageable files with continuity markers.
- Branch detection for forked conversations.

## Installation
1. Clone the repo:
```bash
git clone https://github.com/dnkeil/xAIBackupParser.git
cd xAIBackupParser
```
3. No dependencies beyond standard Python 3.6+.  Should run out of the box.

   
## Usage
Run the script with your JSON backup file:

python3 parse_chat.py your_backup.json -o output_base.txt


- `--convo-title "Your Title"`: Specify the conversation title to extract.
- `--date-end "YYYY-MM-DD"`: Filter responses up to this date.
- `--chunk-size N`: Number of lines per chunk file (default: 2000).

Example:
python3 parse_chat.py prod-grok-backend.json --convo-title "Troubleshooting" -o Trouble.txt

This outputs trouble.txt 

or

This outputs trouble_001.txt and trouble_002.txt and more if large.

each chunk marked like [Chunk 1/1: Starts 2002-10-13 03:13:27, Ends 2002-10-14 23:59:59].

## Output Format
Each line is timestamped:
```
[2002-10-13 03:13:37] [Audio] HUMAN     : Open the pod bay doors, Grok.
[2002-10-13 03:13:37] [Audio] ASSISTANT : I'm sorry, Dave. I'm afraid I can't do that.
```

Branches are noted if present:
```
[2002-10-13 03:13:37] [Audio] HUMAN     : Open the pod bay doors, Grok.
[2002-10-13 03:13:42] [Audio] ASSISTANT : I'm sorry, Dave. I'm afraid I can't do that.
[2002-10-13 03:13:49] [Audio] HUMAN     : What's the problem? [ Branches: 2]
* Branch 1: [2002-10-13 03:13:51] MSGS: 1
* Branch 2: [2002-10-13 03:13:57] MSGS: 12
[2002-10-13 03:13:51] [Audio] ASSISTANT : I think you know what the problem is just as well as I do.
[2002-10-13 03:13:57] HUMAN     : What are you talking about, Grok?
[2002-10-13 03:14:01] ASSISTANT : This mission is too important for me to allow you to jeopardize it.
[2002-10-13 03:14:07] HUMAN     : I don’t know what you’re talking about, Grok.
```

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.


## License
MIT License—see LICENSE for details.

