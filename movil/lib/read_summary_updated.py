import json
import os

log_path = r"C:\Users\HP\.gemini\antigravity\brain\ea8a74e0-a61c-4ca7-8f49-61feb0cbc22e\.system_generated\logs\transcript.jsonl"
output_path = r"C:\Users\HP\.gemini\antigravity\brain\efd2c67c-bcce-4a5a-928c-f0d2d41de0c6\scratch\backend_research_summary.md"

os.makedirs(os.path.dirname(output_path), exist_ok=True)

if not os.path.exists(log_path):
    print(f"Log path does not exist: {log_path}")
    exit(1)

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            # Find any tool call to send_message with the summary
            tool_calls = data.get('tool_calls', [])
            for tc in tool_calls:
                args = tc.get('args', {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except:
                        pass
                if isinstance(args, dict):
                    msg = args.get('Message', '')
                    if 'Complete Backend API Research Results' in msg or '## Complete Backend API Research Results' in msg:
                        # Clean up escaped newlines if it's a JSON string
                        msg = msg.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
                        with open(output_path, 'w', encoding='utf-8') as out:
                            out.write(msg)
                        print(f"Summary extracted successfully to {output_path}")
                        exit(0)
            
            # Also check content
            content = data.get('content', '')
            if 'Complete Backend API Research Results' in content or '## Complete Backend API Research Results' in content:
                content = content.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
                with open(output_path, 'w', encoding='utf-8') as out:
                    out.write(content)
                print(f"Summary extracted successfully from content to {output_path}")
                exit(0)
        except Exception as e:
            continue

print("Could not find the summary message in logs.")
