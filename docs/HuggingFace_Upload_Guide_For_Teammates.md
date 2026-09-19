# Hugging Face Model Upload Guide (For Teammates)

Hello Team! We are standardizing our Sinhala-Script LangID project. Since large machine learning models (like XLM-R, NLLB, ConLID) are too large for GitHub (over 50MB), we are hosting them on **Hugging Face**. 

To make our project perfectly reproducible by anyone, we need your fine-tuned models uploaded. Please follow these exact steps to upload your model to your own free Hugging Face account and send us the URL.

---

### Step 1: Create a Hugging Face Account
If you don't already have one, go to [Hugging Face](https://huggingface.co/join) and create a free account.

### Step 2: Create a Write-Access Token
To upload models via the terminal, you need an access token.
1. Log into your Hugging Face account.
2. Go to **Settings** (Click your profile picture in the top right -> Settings).
3. On the left menu, click **Access Tokens**.
4. Click **Create new token**.
5. Name it something like `LangID-Upload` and set the Type to **Write**.
6. Copy the token. **Do not lose this!**

### Step 3: Prepare your Models
1. Pull the latest code from the `Project-standardize` branch on our GitHub repository.
2. Locate your large fine-tuned model files (e.g., `.bin`, `.pt`, `.safetensors`, `.pkl`).
3. Move your model files into the **`models/`** directory in the root of the project folder on your laptop. 
   *(Note: The script is fully automated and will scan the `models/` folder and upload any model files it finds there.)*

### Step 4: Run the Upload Script
1. Open your terminal (or VS Code terminal) in the root of the project directory.
2. Export your Hugging Face token to your environment variables. 
   - **On Windows (PowerShell):**
     ```powershell
     $env:HF_TOKEN="paste_your_token_here"
     ```
   - **On Mac/Linux:**
     ```bash
     export HF_TOKEN="paste_your_token_here"
     ```
3. Run the automated upload script:
   ```bash
   python scripts/upload_to_huggingface.py
   ```
4. The script will automatically create a repository under your Hugging Face username (e.g., `YourUsername/FastText-Sinhala-Script-LID`) and upload all the models inside your `models/` folder.

### Step 5: Send the URL!
Once the upload finishes, the terminal will print out a link to your Hugging Face profile. 
1. Go to your Hugging Face profile.
2. Click on the newly created model repository.
3. Copy the URL from your browser (e.g., `https://huggingface.co/Vihanga/FastText-Sinhala-Script-LID`).
4. **Send this URL to the group!** 

Once we have everyone's URLs, we will write a tiny `download_models.py` script so that our project automatically fetches everyone's models from Hugging Face when it runs. Thank you!
