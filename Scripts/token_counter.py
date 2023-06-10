"""A script to count the number of tokens in the entire repo."""
import tiktoken, os, sys
import argparse

TOKEN_BATCH_SIZE = 1000
TOKEN_PRICE = 0.03
token_encodings = tiktoken.encoding_for_model("gpt-4")


def get_skprompt_template(directory):
    """Get the skprompt.txt file from the folder and return it as a string."""
    with open(directory + '/skprompt.txt', 'r') as f:
        return f.read()
    
def get_token_count(template):
    """Get the token count from the template."""
    return len(token_encodings.decode(token_encodings.encode(template)))

def search_directory(directory, depth=0):
    """From the directory, loop through every folder and subfolder and count the tokens of the skpompt template."""
    print(f'Searching directory at depth {depth}: ' + directory.split('/')[-1])
    token_count = 0

    #Get all repo items
    items = os.listdir(directory)
    #Remove the .git folder from the list of items if it exists
    if '.git' in items:
        items.remove('.git')
    #Make sure each item is a folder
    folders = [item for item in items if os.path.isdir(os.path.join(directory, item))]


    for folder in folders:
        """
        Check to see if this folder has a skprompt.txt file in it. If not, then it has more skills folders in it.
        We'll need to search through those folders as well.
        """
        folder_path = os.path.join(directory, folder)
        if 'skprompt.txt' not in os.listdir(folder_path):
            token_count += search_directory(folder_path, depth=depth+1)
        else:
            print(f'Searching directory at depth {depth+1}: ' + folder_path.split('/')[-1])
            template = get_skprompt_template(folder_path)
            token_count += get_token_count(template)

    return token_count

def main(directory):
    """Main function."""
    token_count = search_directory(directory)
    print('Total tokens: ' + str(token_count))

    estimated_price = round(float(token_count/TOKEN_BATCH_SIZE*TOKEN_PRICE), 2)
    print('Estimated price: $' + str(estimated_price))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Count the number of tokens in a repo.')
    parser.add_argument('directory', type=str, help='The directory to search.')
    parser.add_argument('--batch_size', type=int, help='The batch size of the model.', default=TOKEN_BATCH_SIZE)
    parser.add_argument('--token_price', type=float, help='The price per token batch size.', default=TOKEN_PRICE)
    args = parser.parse_args()

    main(args.directory)
