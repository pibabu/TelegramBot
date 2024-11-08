import ell

ell.init(store="./logdir", autocommit=True, verbose=True)


@ell.simple(model="gpt-4o-mini", temperature=0.9)
def haiku(usermessage: str, style: str):
    """respond with haiku."""
    return f"{usermessage} in {style} style!"


# Example usage
haiku_result = haiku(usermessage="ninja frog", style="daaaaark")
print(haiku_result)
