import datetime
import os
import time
import dotenv
import requests
import json
import argparse

dotenv.load_dotenv(override=True)

debug = False
raidbots_key = os.getenv("RAIDBOTS_KEY")
raidbots_url = os.getenv("RAIDBOTS_HOST")
mimiron_url = os.getenv("MIMIRON_HOST")
headers = {
  "Content-Type": "application/json",
  "User-Agent": "Khazak APL tester"
}

def check_sim_status(job_id, interval=5):
    url = f"{raidbots_url}/api/job/{job_id}"
    while True:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            job_data = response.json()
            if debug:
              print(job_data)
            job_status = job_data.get("job", {}).get("state")
            if job_status == "complete":
                print("Job is complete.")
                return job_data
            elif job_status == "failed":
                print("Raidbots error")
                return
            else:
                print(f"Job is not yet complete. Progress: {job_data.get('job', {}).get('progress')} Checking again in {interval} seconds...")
        else:
            print(f"Failed to get job state with status code {response.status_code}")
            return
        
        time.sleep(interval) 


def get_sim_result(report_code, style, label="", save_path=".\\results"):
  url = f"{raidbots_url}/reports/{report_code}/index.html"
  response = requests.get(url)
  if response.status_code == 200:
    if not os.path.exists(save_path):
      os.makedirs(save_path)
    file_path = os.path.join(save_path, f"{datetime.datetime.now().strftime('%d%m%Y %H%M')}_{label}{style}_report_{report_code}.html")
    with open(file_path, 'wb') as file:
      file.write(response.content)
    print(f"Report downloaded successfully and saved to {file_path}")
  else:
    print(f"Failed to download report with status code {response.status_code}")


def add_apl_to_profiles(file_path, apl):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    new_lines = []
    for line in lines:
        new_lines.append(line)
        if line.startswith("talents="):
            new_lines.append('\n' + apl + '\n')
    
    return new_lines

def read_apl(apl_path="./profiles/apl.inc"):
   with open(apl_path, 'r') as file:
      return file.read()


def sim(simc_input, style, label, ptr=False):
  body = {
    "type": "advanced",
    "apiKey": raidbots_key,
    "advancedInput": simc_input,
    "simcVersion": "latest",
  }
  raidbots_host = mimiron_url if ptr else raidbots_url
  response = requests.post(raidbots_host + "/sim", headers=headers, data=json.dumps(body).encode("utf8"))

  print(response.json())
  sim_id = response.json()["simId"]
  print(sim_id)

  if response:
    if sim_id:
        result = check_sim_status(sim_id)
        print(result)
        get_sim_result(sim_id, style, label)
    else:
        print("sim ID not found in the response.")
  else:
      print("Failed to send simulation request.")

def find_profiles_for_style(style):
  profiles = []
  for file in os.listdir(f"./profiles/{style}/"):
    if file.endswith(".simc"):
      profiles.append(file)
  return profiles

def find_styles():
  with os.scandir("./profiles") as styles:
    return [style.name for style in styles if style.is_dir() and style.name is not style]

def sim_runner(args):
  apl = read_apl() if not args.defaultAPL else ""

  fight_styles = find_styles()

  for style in fight_styles:
    simc_input = [f"fight_style={style}\n"]
    profiles = find_profiles_for_style(style)
    for profile in profiles:
      simc_input += add_apl_to_profiles(f"./profiles/{style}/{profile}", apl)
      simc_input += "\n"

    simc_input = "".join(simc_input)
    sim(simc_input, style, args.label, args.ptr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip", help="Skip the profiles for the given style")
    parser.add_argument("--label", help="Adds a prefix to the report file name")
    parser.add_argument("--defaultAPL", help="Use the default APL", action="store_true")
    parser.add_argument("--ptr", help="Use mimiron", action="store_true")
    args = parser.parse_args()

    sim_runner(args)