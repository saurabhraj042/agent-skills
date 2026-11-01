import sys,json,pathlib
# usage: build_report.py data.json out.html
tpl=pathlib.Path(__file__).resolve().parent.parent/"references"/"report-template.html"
data=json.load(open(sys.argv[1]))
blob=json.dumps(data,ensure_ascii=False).replace("</","<\\/")
html=tpl.read_text().replace("__DATA__",blob,1)
pathlib.Path(sys.argv[2]).write_text(html)
print("wrote",sys.argv[2],len(html),"bytes")
