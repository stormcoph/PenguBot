import glob

print([x.split("/")[-1].split("\\")[-1] for x in glob.glob("../../assets/models/*.engine")])