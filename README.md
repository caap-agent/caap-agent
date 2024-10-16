# CAAP: Context-Aware Action Planning Prompting to Solve Computer Tasks with Front-End UI Only

***

## Introduction
This repository contains code for CAAP Agent, intended for use in MiniWoB++ and WebShop.
This README.md file provides an overview of the contents. Please refer to the README.md files in each environment folder for detailed information on each environment.

***

## Comparison with other image-only methods
* ### for solving MiniWoB++ problems

<div align="center">

| Method | Modality | Image datasize | Demo datasize | Reported SR | Reported tasks |
| :-: | :-: | :-: | :-: | :-: | :-: |
| Human | Image | - | - | 93.5\% | 104 |
| CC-Net (no DOM) | Image | 0 | 2.4M | 24.0\% | 104 |
| Pix2Act | Image | 0 | 1.3M | 96.2\% | 59 |
| SeeClick | Image | 0 | 2.8K | 69.4\% | 55 |
| CAAP | Image | 1.8K | 0.1K | 94.5\% | 73 |
</div>


<!-- ### <p style="text-align:center;">for solving WebShop problems</p> -->
* ### for solving WebShop problems

<div align="center">

| Method | Modality | Image datasize | Demo datasize | Task score |
| :-: | :-: | :-: | :-: | :-: |
| Human | Image | - | - | 82.1 |
| Pix2Act | Image | 0 | 1K | 46.7 |
| CAAP | Image | 0.3K | 1 | 62.3 |
</div>



***
## Common Setup Instructions
### Prerequisites
```python
git clone https://github.com/caap-agent/caap-agent.git
cd caap-agent
# requirements was created at Pyhon 3.9.13
python -m pip install -r requirements.txt
```

***
### Download checkpoints for vision model
- ../vision_model_checkpoints [file location example](#directory-tree)  
Download the checkpoint folder through this [**link**](https://drive.google.com/file/d/1BNEwmUBMoy0DRtcISvpKRTciXh6OP5B5/view?usp=drive_link) and unzip it, placing it in the parent folder.

***
### Fill in the Credential information
- ../.credentials.json with the following format json [file location example](#directory-tree)
```
{
    "OPENAI_API_BASE": <YOUR_OPENAPI_API_BASE>,
    "OPENAI_API_KEY": <YOUR_OPENAPI_API_KEY>,
    "OPENAI_API_TYPE": "azure",
    "OPENAI_API_VERSION": "2024-02-15-preview",
    "OPENAI_API_ENGINE_GPT4": "gpt-4-0125-preview",
    "OPENAI_API_ENGINE_GPT3": "gpt-35-turbo-v1106",
    "HTTP_PROXY": <HTTP_PROXY>, # optional
    "HTTPS_PROXY": <HTTPS_PROXY>, # optional
    "NO_PROXY": "", # optional
    "REQUESTS_CA_BUNDLE": "", # optional
}
```

- OPENAI_API_BASE : Base path of Azure OpenAI API
- OPENAI_API_KEY : Secret Key of Azure OpenAI API

Even if you habe entered the correct information, if it is not working,
Please modify 2 points, according to your own environments, it may vary.
1. 355th line of src>supports>caap_prompter_support.py 'openai.ChatCompletion.create'
2. 451th line of src>supports>demo_scripter_support.py 'openai.ChatCompletion.create'

***
### Directory tree
```
├== caap-agent
│   ├== for_visual_observer
│   │   ├== datasets
│   │   ├== generate_dataset_code
│   │   └== model_training_code
│   ├== miniwob++
│   ├== webshop
│   ├── LICENSE
│   ├── README.md
│   ├── required_modules.txt
│   └── requirements.txt
├== vision_model_checkpoints
│   ├== base
│   │   ├── hub
│   │   └── yolov8x.pt
│   ├== miniwob++
│   │   ├── pix2struct_model
│   │   └── yolo_model
│   └== webshop
│       ├── pix2struct_model
│       └── yolo_model
└── .credentials.json
```


- caap-agent > for_visual_observer : Datasets that has been trained on visual observer and code for generating the dataset and training the model.
- caap-agent > miniwob++ : Code for MiniWoB++ Environment.
- caap-agent > webshop : Code for Webshop Environment.
- caap-agent > required_modules.txt : This file contains a list of Python modules that must be installed in order to run this project successfully.
- vision_model_checkpoints : Visual Observer Checkpoints used in each environment.


> ## ✔ **NOTE** 
>*  Do not click on other windows until the Environment's window opens.
>Pressing another window while the Environment's window opens will cause the other window to be mistaken for the Environment's window.
>* The models required for the Visual Observer are supposed to run on the CPU, so it may be slow depending on the environment. If necessary, Please check the src>supports>screen_commentator.py file and use a GPU or other technology to improve speed.


> ### Optional Steps
> - If you want to train a vision model using the dataset we provide, you neet to unzip them.
>   - for_visual_observer > datasets > *.zip
>   - for_visual_observer > generate_dataset > miniwob++ > _completed.zip
> - for a yolo model training
>   ```python
>   python3 train_yolo_for_ui_detection.py
>   ```
> - for a pix2struct model training
>   ```python
>   deepspeed --num_gpus {number_gpus} train_pix2struct_for_ui_understanding.py
>   ```

***
## License
[License](LICENSE)
