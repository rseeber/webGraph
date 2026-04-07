import datetime

file = None

# set the log file. f should be a string to a local path file
def setFile(f):
    global file
    file = f

# Print's msg, prepended with a timestamp. It also saves it to the log file.
def write(msg):
    # Create the output
    myTime = datetime.datetime.now().strftime("%b %d %Y %H:%M:%S")
    ouput = f"[{myTime}]: {msg}"
    # Print it
    print(ouput)
    # Log it
    with open(file, "a") as f:
        f.write(ouput+"\n")

# Example Usage (preppend module to both functions, of course)
if __name__ == "__main__":
    setFile("example/log.txt")
    write("hello, world")