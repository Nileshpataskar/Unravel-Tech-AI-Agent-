import tiktoken 
encoding= tiktoken.get_encoding("cl100k_base")
text='hi'
tokens=encoding.encode(text)

print(tokens)
print(len(tokens))