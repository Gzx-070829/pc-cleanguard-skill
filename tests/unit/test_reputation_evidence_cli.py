import io,json,unittest
from tempfile import TemporaryDirectory
from contextlib import redirect_stdout,redirect_stderr
from pathlib import Path
from pc_cleanguard.cli import main

class EvidenceCliTest(unittest.TestCase):
    def test_validate_and_stats(self):
        pack=Path(__file__).resolve().parents[2]/"data/reputation/evidence_pack.zh-CN.json"
        for command in ("validate","stats"):
            out=io.StringIO()
            with redirect_stdout(out),redirect_stderr(io.StringIO()): self.assertEqual(0,main(["reputation","evidence",command,"--input",str(pack)]))
            data=json.loads(out.getvalue()); self.assertEqual(0,data["execution_gating_eligible_count"])
    def test_validate_rejects_execution_authorized_true(self):
        source=Path(__file__).resolve().parents[2]/"data/reputation/evidence_pack.zh-CN.json"
        records=json.loads(source.read_text(encoding="utf-8")); records[0]["execution_authorized"]=True
        with TemporaryDirectory() as directory:
            path=Path(directory)/"bad.json"; path.write_text(json.dumps(records),encoding="utf-8")
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                self.assertEqual(2,main(["reputation","evidence","validate","--input",str(path)]))
