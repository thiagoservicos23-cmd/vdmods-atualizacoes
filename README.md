# Atualizações VDMODS

Repositório público de distribuição das atualizações VDMODS. Os executáveis são anexados a **Releases**, sem incluir código privado, credenciais Firebase, tokens dos painéis ou chaves do provedor.

O aplicativo consulta `thiagoservicos23-cmd/vdmods-atualizacoes`. Cada release estável precisa conter:

- `VDMODS-<versão>-portable.zip`: exatamente VDMODS.exe, vapor-backend.exe e update-manifest.json;
- `SHA256SUMS`: SHA-256 dos arquivos publicados;
- `VDMODS-<versão>-setup.exe`: instalador para novos usuários.

Use uma compilação nova para cada atualização: build_id e built_at precisam ser novos. Só alterar o nome/tag do release não atualiza o aplicativo. O pacote não pode ser um ZIP da pasta inteira do projeto.

## Publicar

É necessário Python 3.10+, Git e GitHub CLI autenticado na conta com acesso ao repositório. Instale o gh por uma fonte oficial e faça `gh auth login` se necessário. Não coloque tokens em arquivos ou no comando.

Coloque os três arquivos acima e opcionalmente NOTAS.md em uma pasta fora do histórico Git. Valide:

```powershell
python publicar.py --pasta "..\VDMODS-RELEASE" --validar
```

Para criar o repositório público, enviar este conteúdo inicial e publicar a primeira release:

```powershell
python publicar.py --pasta "..\VDMODS-RELEASE" --criar-repositorio
```

Nas próximas versões use o mesmo comando sem `--criar-repositorio`. O script valida checksums e manifesto antes de qualquer publicação, envia os anexos para um rascunho e só então publica a release estável. Não há workflow automático que recompile ou sobrescreva os executáveis enviados.

## Migração dos clientes anteriores

As primeiras compilações VDMODS consultavam o repositório do Vapor Max. Para alcançá-las, publique uma vez o MESMO ZIP VDMODS novo em uma release estável de `thiagoservicos23-cmd/atualizacaovapor`, junto do SHA256SUMS correspondente, preservando os anexos Vapor Max. Instale/atualize esse pacote: depois ele passa a consultar este repositório separado. Sem essa transição ou instalação manual, o cliente antigo não descobre a mudança de repositório sozinho.

Documentação oficial: [criar repositório](https://cli.github.com/manual/gh_repo_create), [criar release](https://cli.github.com/manual/gh_release_create), [publicar rascunho](https://cli.github.com/manual/gh_release_edit).
