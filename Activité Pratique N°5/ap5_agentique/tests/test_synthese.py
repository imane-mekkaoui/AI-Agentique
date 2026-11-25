import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ap5.garantie import consulter_garantie, extraire_numero_serie
from ap5.rag import rag_multimodal
from ap5.routage import classer_demande


class SyntheseSAV(unittest.TestCase):
    def test_exemple_documentation(self):
        q = (
            "Mon imprimante PX-200 affiche un voyant clignotant. "
            "Que signifie le pictogramme sur la photo jointe ?"
        )
        self.assertEqual(classer_demande(q, "img_px200_01"), "documentation")
        obs = rag_multimodal(q, image_ref="img_px200_01")
        self.assertIn("img_px200_01", obs)
        self.assertIn("bourrage", obs.casefold())

    def test_exemple_garantie(self):
        q = (
            "Est-ce que mon imprimante est encore sous garantie ? "
            "Son numéro de série est PX200-0042."
        )
        self.assertEqual(classer_demande(q), "garantie")
        self.assertEqual(extraire_numero_serie(q), "PX200-0042")
        obs = consulter_garantie("PX200-0042", aujourdhui=date(2026, 11, 25))
        self.assertIn("sous_garantie", obs)

    def test_garantie_expiree(self):
        obs = consulter_garantie("PX200-0001", aujourdhui=date(2026, 11, 25))
        self.assertIn("expiree", obs)


if __name__ == "__main__":
    unittest.main()
