import tempfile
import unittest
from pathlib import Path

from defi_desktop import PainelDefi, _partes_documento


class PaginaTeste:
    def update(self):
        pass


class DefiTest(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.arquivo = Path(self.pasta.name) / "progresso.json"
        self.painel = self.abrir()

    def abrir(self):
        return PainelDefi(PaginaTeste(), lambda _: "#888888", caminho_progresso=self.arquivo)

    def test_erros_persistem_e_revisao_abre_questao_original(self):
        painel = self.painel
        painel.opcao_selecionada = 0
        painel._conferir()
        painel._conferir()
        reaberto = self.abrir()
        self.assertEqual(reaberto.erros["portrait:0"]["erros"], 2)
        reaberto._mostrar_revisao()
        self.assertFalse(reaberto.corpo_curso.visible)
        reaberto._revisar_atividade(0, 0)
        self.assertTrue(reaberto.corpo_curso.visible)
        reaberto.opcao_selecionada = 1
        reaberto._conferir()
        final = self.abrir()
        self.assertTrue(final.erros["portrait:0"]["revisado"])
        self.assertIn("portrait:0", final.concluidas)
        self.assertEqual(final.erros["portrait:0"]["erros"], 2)

    def test_sem_resposta_nao_conta_como_erro(self):
        self.painel._conferir()
        self.assertEqual(self.painel.erros, {})

    def test_formatos_novos_renderizam_e_oral_exige_autoavaliacao(self):
        painel = self.painel
        for ui, unidade in enumerate(painel.curso):
            painel.unidade_atual = ui
            for ai, atividade in enumerate(unidade["atividades"]):
                painel.atividade_atual = ai
                painel._renderizar_atividade()
                if atividade.get("audio") and atividade.get("opcoes"):
                    self.assertEqual(len(painel.area_resposta.controls), len(atividade["opcoes"]) + 1)
                if atividade.get("oral"):
                    painel._conferir()
                    self.assertNotIn(painel._chave(), painel.concluidas)
                    for check in painel.checks_orais:
                        check.value = True
                    painel._conferir()
                    self.assertIn(painel._chave(), painel.concluidas)
        self.assertEqual(sum(len(u["atividades"]) for u in painel.curso), 288)

    def test_ocultar_resposta_reabilita_nova_tentativa(self):
        self.painel.opcao_selecionada = 1
        self.painel._conferir()
        self.painel._mostrar_resposta()
        self.painel._tentar_novamente()
        self.assertFalse(self.painel.gabarito.visible)
        self.assertTrue(self.painel.botao_conferir.visible)
        self.assertIsNone(self.painel.opcao_selecionada)

    def test_documento_separa_falas_em_linhas(self):
        partes = _partes_documento(
            "La serveuse demande : « Vous avez choisi ? » Camille répond : « Oui. » Fin."
        )
        self.assertEqual(5, len(partes))
        self.assertEqual(2, sum(eh_fala for _, eh_fala in partes))
        self.assertEqual("« Vous avez choisi ? »", partes[1][0])

        self.painel.unidade_atual = next(
            indice for indice, unidade in enumerate(self.painel.curso)
            if unidade["titulo"] == "Au restaurant"
        )
        self.painel._renderizar(atualizar=False)
        self.assertEqual(7, len(self.painel.documento_texto.controls))
        self.assertEqual(3, sum(controle.bgcolor is not None for controle in self.painel.documento_texto.controls))

    def test_tipo_de_atividade_reserva_largura_fixa_antes_dos_passos(self):
        self.assertEqual(112, self.painel.caixa_tipo_atividade.width)
        self.assertIs(self.painel.tipo_atividade, self.painel.caixa_tipo_atividade.content)

    def test_curso_inclui_situacoes_praticas_de_paris(self):
        titulos = {unidade["titulo"] for unidade in self.painel.curso}
        self.assertEqual(22, len(self.painel.curso))
        self.assertTrue({
            "Arriver à Paris",
            "Prendre le métro",
            "Lire les rues et les panneaux",
            "À la boulangerie et au café",
            "Faire des achats",
            "Visiter les musées et monuments",
            "À la pharmacie",
            "En cas de problème",
            "Parler avec les Parisiens",
        }.issubset(titulos))


if __name__ == "__main__":
    unittest.main()
