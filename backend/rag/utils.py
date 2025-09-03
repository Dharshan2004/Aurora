'''
UTILITY FUCNCTIONS FOR RAG
'''


'''
Function to carry out light cleaning of text
'''

def clean_text(text: str):
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()