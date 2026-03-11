import argparse

from svg.pipeline import generate_visualization
from svg.ui.app import SoundVisualisationApp

# main entry point for application, 
# handles command line with arguments for input and output file, otherwise starts GUI

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--output")
    args = parser.parse_args()

    if args.input and args.output:
        generate_visualization(args.input, args.output)
        print(f"Saved: {args.output}")
    else:
        app = SoundVisualisationApp()
        app.mainloop()


if __name__ == "__main__":
    main()
