"""Conteúdo compartilhado entre o aplicativo e o site."""

import json
import re
from pathlib import Path


RAIZ = Path(__file__).resolve().parent
PADRAO_PALAVRA = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿŒœ]+(?:['’][0-9A-Za-zÀ-ÖØ-öø-ÿŒœ]+)*")


def _preparar_escuta(atividade: dict) -> dict:
    if not atividade.get("audio") or atividade.get("oral"):
        return atividade
    if atividade.get("opcoes"):
        atividade.setdefault("instrucao", "Ouça quantas vezes precisar e responda sobre o que foi dito.")
        return atividade
    if not atividade.get("respostas"):
        return atividade

    audio = atividade["audio"]
    palavras = list(PADRAO_PALAVRA.finditer(audio))
    if len(palavras) < 2:
        return atividade
    inicio, fim = palavras[-2].start(), palavras[-1].end()
    resposta = audio[inicio:fim]
    atividade.update({
        "tipo": "écoute à trous",
        "pergunta": f"Écoute et complète : « {audio[:inicio]}___{audio[fim:]} »",
        "instrucao": "Ouça e escreva somente as palavras que faltam.",
        "respostas": [resposta],
        "resposta": resposta,
    })
    return atividade


def carregar_curso():
    curso = json.loads((RAIZ / "defi_data.json").read_text(encoding="utf-8"))
    curso.extend(json.loads((RAIZ / "defi_viagem.json").read_text(encoding="utf-8")))
    pratica = json.loads((RAIZ / "defi_pratica.json").read_text(encoding="utf-8"))
    for unidade in curso:
        # Acrescentar preserva os índices do progresso já salvo no site.
        unidade["atividades"].extend(pratica.get(unidade["id"], []))
        unidade["atividades"] = [_preparar_escuta(atividade) for atividade in unidade["atividades"]]
    return curso


if __name__ == "__main__":
    curso = carregar_curso()
    conteudo = "// Gerado por python curso_defi.py.\nwindow.CURSO_DEFI = "
    conteudo += json.dumps(curso, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (RAIZ / "docs" / "defi-data.js").write_text(conteudo, encoding="utf-8")
    print(f"{len(curso)} unidades, {sum(len(u['atividades']) for u in curso)} atividades")
