from partie2.rag_runtime import repondre_depuis_tableau_frequence
from partie2 import api
from fastapi.testclient import TestClient


def test_repondre_depuis_frequence_cite_seulement_les_operations_correspondantes():
    sources = [
        {
            "metadata": {"content_type": "text", "page_number": 83},
            "contenu": "Le tableau présente plusieurs fréquences.",
        },
        {
            "metadata": {"content_type": "table", "page_number": 83},
            "contenu": (
                "Opération : Graisser les supports. | Fréquence : 30 jours\n"
                "Opération : Contrôler la tension des chaînes. | Fréquence : 30 jours\n"
                "Opération : Contrôler l'installation pneumatique. "
                "| Fréquence : 60 jours"
            ),
        },
    ]

    reponse = repondre_depuis_tableau_frequence(
        "Quels contrôles faire tous les 30 jours ?", sources
    )

    assert reponse is not None
    assert "Graisser les supports. [2]" in reponse
    assert "Contrôler la tension des chaînes. [2]" in reponse
    assert "installation pneumatique" not in reponse


def test_repondre_depuis_tableau_signale_une_frequence_absente():
    sources = [
        {
            "metadata": {"content_type": "table", "page_number": 83},
            "contenu": (
                "Opération : Graisser les supports. | Fréquence : 30 jours"
            ),
        }
    ]

    reponse = repondre_depuis_tableau_frequence(
        "Quels contrôles faire tous les 45 jours ?", sources
    )

    assert reponse is not None
    assert "ne liste aucune opération" in reponse


def test_repondre_depuis_tableau_sabstient_si_le_tableau_est_non_structure():
    sources = [
        {
            "metadata": {"content_type": "table", "page_number": 83},
            "contenu": "Fréquence | Opération : Graisser les supports ♦",
        }
    ]

    assert (
        repondre_depuis_tableau_frequence(
            "Quels contrôles faire tous les 30 jours ?", sources
        )
        is None
    )


def test_api_sert_une_image_extraite_et_refuse_les_chemins_hors_dossier(tmp_path, monkeypatch):
    image = tmp_path / "image-test.png"
    image.write_bytes(b"image de test")
    monkeypatch.setattr(api, "DOSSIER_IMAGES", tmp_path)
    client = TestClient(api.create_app(agent_factory=lambda: object()))

    with client:
        response = client.get("/api/images/image-test.png")
        assert response.status_code == 200
        assert response.content == b"image de test"
        assert client.get("/api/images/introuvable.png").status_code == 404
        assert client.get("/api/images/../api.py").status_code == 404
