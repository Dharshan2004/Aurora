'''
UTILITY FUNCTIONS FOR RAG
'''

# -- Clean Text --

def clean_text(text: str):
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()