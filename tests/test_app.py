import unittest,tempfile
from pathlib import Path
import app
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  app.DB=Path(tempfile.gettempdir())/"rsg_bi_test2.db"
  if app.DB.exists(): app.DB.unlink()
  app.initialize_database(); cls.client=app.app.test_client()
 def ask(self,q): return self.client.post("/api/ask",json={"question":q})
 def test_total(self): self.assertEqual(self.ask("total revenue").status_code,200)
 def test_product(self): self.assertEqual(self.ask("which product generated highest revenue").status_code,200)
 def test_monthly(self): self.assertEqual(self.ask("monthly revenue trend").status_code,200)
 def test_region(self): self.assertEqual(self.ask("highest sales region").status_code,200)
 def test_invalid(self): self.assertEqual(self.ask("tell me a joke").status_code,400)
 def test_edge_months(self): self.assertEqual(self.ask("compare January").status_code,400)
if __name__=="__main__": unittest.main()
