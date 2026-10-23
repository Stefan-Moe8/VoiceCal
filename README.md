# VoiceCal

## Setup Instructions

#### 1. Install Git
Make sure Git is installed on your system (done via the terminal):

```bash
git --version
```
If not installed, you can download it here:
https://git-scm.com/install/

#### 2. Clone the repository

```bash
git clone https://github.com/Stefan-Moe8/VoiceCal.git
```

#### 3. Move into the folder

```bash
cd VoiceCal
```
can open it in VS Code with:
```bash
code .
```

### Daily Workflow

#### 1. Pull the latest changes

```bash
git pull
```

#### 2. Add your changes

```bash
git add .
```
#### 3. Commit changes
```bash
git commit -m "what you did"
```

#### 5. Push changes

```bash
git push
```
### .env.example

```bash
# Copy this file to .env (in the same folder as the notebooks) and paste your key.
OPENAI_API_KEY=sk-your-key-here
```

## How to run the app

## Models and providers used

### Usage and cost summary

The price for gpt-6-luna is $0.50 per million output tokens and $0.10 per million input tokens. The price for gpt-4o-transcribe-mini is $1.25 per million input tokens and $5.00 per million output tokens. As a rough estimate, if we have 200 input and output tokens per prompt and 1000 prompts, that would be 200,000 tokens in total. The total cost would be about $1.37.

## AI-use disclosure

