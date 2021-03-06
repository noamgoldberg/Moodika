import argparse


def parse_args(args_string_list):
    """
    Parses input arguments.
    Returns a structure with all the input arguments
    """
    # Interface definition
    parser = argparse.ArgumentParser(description="Input your mood to generate spotify playlist.",
                                     formatter_class=argparse.RawTextHelpFormatter)

    subparser = parser.add_subparsers(dest='command')

    login = subparser.add_parser('login', help=f'Update client information. "login -h" for more information')
    login.add_argument('--id', type=str, required=False)
    login.add_argument('--secret', type=str, required=False)

    update = subparser.add_parser('input', help=f'Input to pass to model. "input -h" for more information')
    update.add_argument('-t', '--text', type=str, help='Input text')
    update.add_argument('-p', '--popularity', type=int, required=False, help=f'Desired popularity')
    update.add_argument('-l', '--length', type=int, required=False, help=f'Desired length of playlist', default=100)
    update.add_argument('-v', '--verbose', type=int, required=False,
                        help=f'Increase verbosity to show more information during playlist generation', default=0)

    return parser.parse_args(args_string_list)
