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
### .env.example
```bash
# Copy this file to .env (in the same folder as the notebooks) and paste your key.
OPENAI_API_KEY=sk-your-key-here
```
## Daily Workflow

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
#### Note:
Can check whether files are up to date and whether you have uncommitted work using
```bash
git status
```
### How to fix a Git merge conflict error

#### 1. Stash your local changes

```bash
git stash
```

This temporarily saves your uncommitted changes so they don't interfere with pulling updates.

#### 2. Pull the latest changes

```bash
git pull
git status
```
If Git reports merge conflicts, resolve them before proceeding.
#### 3. Restore your local changes
```bash
git stash pop
git status
```
If conflicts occur, resolve them before continuing. If `git stash pop` encounters conflicts, Git generally keeps the stash so you can recover your changes if needed.
#### 4. Manually fix conflicted files
Look for conflict markers such as:
```text
<<<<<<< HEAD
Your current branch's changes
=======
Incoming changes
>>>>>>> branch-name
```
Decide which changes to keep or combine, then remove the conflict markers. Save the files and verify that the resulting code is correct.
#### 5. Stage and commit the resolved changes
```bash
git add .
git commit -m "Resolve merge conflicts"
git push
```
Before committing, review your changes and run relevant tests to ensure the merged code still works.
## How to run the app

## Models and providers used
- Gpt-6-luna
- Gpt-4o Minin TTS
- Gpt-transcribe
### Usage and cost summary

The price for gpt-6-luna is $0.50 per million output tokens and $0.10 per million input tokens. The price for GPT-Transcribe is $0.0045 per minute of audio input being transcribed. The price for GPT-4o Mini TTS is $0.60 per million text input tokens and $12.00 per million audio output tokens. As a rough estimate, if there is 30 seconds of speech input, which creates about 100 input text tokens and about 200 output tokens, 100 going to text-to-speech, per prompt for 1000 prompts, that would cost about $1.37.

### AI-use disclosure
## Tools utilized
LLM: Luna model, used to interpret natural-language scheduling requests and extract structured calendar event information.
Speech-to-Text: gpt-transcribe, used to convert spoken user requests into text.
Text-to-Speech: gpt-4o Mini TTS, used to convert the assistant's responses into spoken audio.
Calendar API: Used to retrieve calendar information, check availability, and create events.

## Scope of Usage
The LLM interprets user requests and extracts relevant information, including event details, including titles, dates, times, durations, and locations.
The LLM identifies missing or ambiguous information and helps generate clarification questions when a request cannot be processed reliably.
Speech-to-text converts spoken requests into text that can be processed by the LLM.
Text-to-speech allows the assistant to communicate confirmations, clarification questions, and error messages verbally.
The calendar integration uses the extracted event information to check availability and create calendar events after appropriate validation and user confirmation.

## Verification Method
The LLM’s event extraction will be evaluated using a dataset of representative scheduling requests with expected outputs.
Model-generated event details will be checked for accuracy, completeness, and correct formatting.
Ambiguous requests, missing information, transcription errors, and scheduling conflicts will be tested to evaluate the assistant’s reliability.
Calendar operations will be verified to ensure events are created with the correct details and only after the required confirmation.
Speech-to-text and text-to-speech functionality will be tested independently and as part of the complete application workflow.
The team will document evaluation results and use them to identify limitations and improve the system.

