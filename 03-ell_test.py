import ell

ell.init(store='./logdir', autocommit=True, verbose=True)

@ell.simple(model="gpt-4o-mini", temperature=0.9)
def haiku(usermessage: str):
    """respond with haiku.""" 
    return f"{usermessage}!"

haiku = haiku("ninja frog")
print(haiku)