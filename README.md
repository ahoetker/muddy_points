# Muddy Points

This project automatically generates a status report for CHE 334 using the Canvas API. 

## Getting Started

The module `cli.py` is the command-line entrypoint for the program. A new report can be created using the `generate`
function:

`python cli.py generate "CHE 334" 1`

### Prerequisites

To use this software in any meaningful way, you would need to be an instructor or TA for a Chemical Engineering course 
at ASU. If you are that kind of person, you should generate a Canvas Developer API key through the 
`Profile > Settings > Approved Integrations` interface.

By default, the program looks for this token in `canvas_token.txt`. The command-line argument to specify a different 
file is `--canvas_token`.

Python `>3.6` is required.

### Installing

After cloning this repository, the dependencies can be installed using `pip`:

`pip install -r requirements.txt`

## Authors

Author | Contact | Github
--- | --- | ---
Andrew Hoetker | ahoetker@me.com | [ahoetker](https://github.com/ahoetker)

## License
MIT License

Copyright (c) [2019] [Andrew Hoetker]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
