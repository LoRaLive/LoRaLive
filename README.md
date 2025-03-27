# LoRaLive: Compact LoRaWAN Traffic Generator

Welcome to the LoRaLive source code repository, that accompanies the paper:

> **LoRaLive: Efficient LoRaWAN Traffic Generation** (to appear in the proceedings)  
> *Vadim Safronov, Richard Mortier*  
> 3rd ACM International Workshop on Testing Distributed Internet of Things Systems (TDIS 2025), co-located with EuroSys 2025.

If you use this code in your research, please cite the paper accordingly.

---

## Overview

LoRaLive is a compact framework for emulating and generating LoRaWAN traffic using Pycom LoPy4 physical nodes, based on previously captured real-world datasets from dense deployments. It includes preprocessing tools to clean, segment, and prepare the dataset for subsequent generation on LoRaWAN physical nodes. 

The LoRalive accuracy was evaluated on [LoED dataset](https://doi.org/10.1145/3419016.3431491):

> *Laksh Bhatia, Michael Breza, Ramona Marfievici, and Julie A. McCann. 2020. LoED: The LoRaWAN at the Edge Dataset. In Proceedings of the 3rd ACM Workshop on Data: Acquisition To Analysis (DATA '20), 7–8.*

---

## Setup & Deployment Instructions

Follow these steps to reproduce LoRaWAN traffic generation with LoRaLive:

### 1. Upload the Dataset

Place your dataset in the `dataset_preprocessing/dataset/` folder. The dataset must follow the format of the LoED dataset.

---

### 2. Preprocess the Dataset

Navigate to the `dataset_preprocessing/` directory and run:

```bash
python3 prepare_dataset.py dataset/01_03_2019.csv
```

This will clean the dataset, remove duplicates, and produce a file named `ul_01_03_2019.csv`.

The IFD regression models are stored in the `inner_delay_regression/` folder and are based on LoPy4 device measurements.  
For other types of LoRaWAN nodes, please measure IFD for your SF/BW/CR unique parameter pairs and retrain a model following **Algorithm 1** from the TDIS paper.

---

### 3. Generate OTAA Device Credentials

Generate a unique OTAA identity for each device found in the dataset:

```bash
python3 gen_dev_credentials.py
```

### 4. Register Devices on a LoRaWAN Server

Use the credentials in `device_credentials.json` to register each device on your LoRaWAN server (e.g., ChirpStack or The Things Stack).  
This can be done manually or via an automated script using the server’s API.


### 5. Split the Dataset into Per-Node CSV traces

To respect regional duty cycles and emulate realistic node behavior, split the dataset into individual device traces:

```bash
python3 csv_splitter_compact.py ul_01_03_2019.csv 36 0
```
Arguments:

- ul_01_03_2019.csv: your cleaned dataset file.

- 36: duty cycle in seconds (e.g., 1% duty cycle → 36s).

- 0: additional delay (use 0 for exact timing replication).

The script will output files like device-0.csv, device-1.csv, etc., into the devices/ folder.

### 6. Configure and Upload Firmware to LoPy4 Devices

The example of physical node files are located under the `physical_node` folder. Each Pycom LoPy4 physical node must include:

- A specific trace file renamed to `device.csv` (e.g., `device-0.csv`).
- The shared `device_credentials.json` file for OTAA credentials.
- A Wi-Fi configuration file `wifi_config.json` for NTP sync, e.g.:

```json
{
  "ssid": "Your_WiFi_SSID",
  "password": "Your_WiFi_Password"
}
```
Upload the contents of the device/ folder to each LoPy4 device, replacing device.csv accordingly.

### 7. Run the Experiment

Power on all physical nodes simultaneously. Each physical node has `eval.py` script that:

- Connects to Wi-Fi and sync with an NTP server.
- Joins the LoRaWAN network via OTAA.
- Transmits packets based on the original dataset timing.

Let the experiment run to completion.  
You may monitor the devices using serial output or collect traffic from your LoRaWAN server.
