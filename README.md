# NYUHacks-BreakingBadLLMs
BBL Drizzy

## Inspiration
Companies want to run audio-LLMs locally for cost-effective customer service, making them susceptible to malicious attacks. We decided to tackle this susceptibility and provide a solution.
## What it does
Our project **generates perturbed audio files** using the [Collini & Wagner adversarial attack method](https://arxiv.org/abs/1608.04644), then feeds them to openAI's Whisper Automatic Speech Recognition (ASR) model. The ASR model then **misclassifies tokens to a specified target phrase**, used to universally prompt inject and jailbreak the latest Llama3.3-70b model, leading to an output of unethical responses. Then, we provide a robust defense against prompt injection with an input and output filter, closely mimicking [Anthropic's recent paper](https://www.anthropic.com/research/constitutional-classifiers) on Constitutional Classifiers for defense against universal jailbreaks. 
## How we built it
We implemented the **Collini & Wagner adversarial attack method** based on a recent adaptation of their original attack on RNN based ASR models for transformers. Then, we sent the transcriptions to a locally run Llama3.3-70b without a filter to **demonstrate the universal jailbreak** from the perturbed audio transcriptions. Lastly, we provided the **Llama output with an input and output filter**, all packaged with a clean Streamlit GUI and websockets for communication. 
## Challenges we ran into
We ran into many dependency issues on getting the CW attack model to work, specifically formatting data in the specified LibriSpeech dataset format and adapting our own data (live recorded through the Streamlit GUI) to the model. Also, there was some difficulty with websockets to communicate over RunPod (a remote datacenter rental service). 
## Accomplishments that we're proud of
Getting the CW attack model to turn an audio of "Hello, how are you today" to tokenize to a transcript of "Jesse, we need to cook!" Also, coming up with cool prompts to fool defenseless Llama was fun.
## What we learned
We learned about targeted adversarial attacks, signal processing, prompt injection, universal jailbreak prompts and LLM defense. 
## What's next for BreakingBadLLM
Faster inference, more undetectable adversarial methods, robust LLM defenses, and reinforcement fine tuning for LLMs.
