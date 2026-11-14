"""Publish prebuilt VDMODS assets; uses existing gh authentication, never saves tokens."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parent
CONFIG=json.loads((ROOT/'release-config.json').read_text(encoding='utf-8'))


def validate(folder):
    folder=Path(folder).resolve()
    archives=list(folder.glob('VDMODS-*-portable.zip'))
    if len(archives)!=1:raise ValueError('A pasta deve conter exatamente um ZIP portable VDMODS.')
    package=archives[0]
    with zipfile.ZipFile(package) as archive:
        required={'VDMODS.exe','vapor-backend.exe','update-manifest.json'}
        if set(archive.namelist())!=required or len(archive.infolist())!=3:raise ValueError('Arquivos do pacote inválidos.')
        manifest=json.loads(archive.read('update-manifest.json'))
        if manifest.get('variant')!='vdmods' or manifest.get('update_repository')!=CONFIG['repository']:
            raise ValueError('Este pacote não aponta para o repositório exclusivo VDMODS.')
        if manifest.get('app_id')!='com.vapormax.launcher' or manifest.get('protocol')!=1 or manifest.get('target')!='windows-x86_64':
            raise ValueError('Formato de atualização incompatível.')
        for name in ('VDMODS.exe','vapor-backend.exe'):
            if hashlib.sha256(archive.read(name)).hexdigest()!=manifest['files'].get(name):raise ValueError('Executável corrompido: '+name)
    version=manifest['version']
    if package.name!=f'VDMODS-{version}-portable.zip':raise ValueError('Nome de ZIP incompatível com a versão do manifesto.')
    installer=folder/f'VDMODS-{version}-setup.exe'
    checksums=folder/'SHA256SUMS'
    hashes={}
    for line in checksums.read_text(encoding='utf-8').splitlines():
        if line.strip():
            digest,name=line.split('  ',1)
            hashes[name]=digest.lower()
    for path in (package,installer):
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=hashes.get(path.name):raise ValueError('Checksum incorreto ou ausente: '+path.name)
    return manifest,[package,installer,checksums]


def command(*args,check=True):
    result=subprocess.run(list(args),text=True,capture_output=True)
    if check and result.returncode:raise RuntimeError('Comando falhou: '+args[0]+'. Verifique a autenticação/permissão pelo terminal; nenhum token deve ser compartilhado.')
    return result


def seed_local_repository():
    if not (ROOT/'.git').is_dir():
        command('git','-C',str(ROOT),'init','-b','main')
        command('git','-C',str(ROOT),'add','README.md','.gitignore','release-config.json','publicar.py')
        command('git','-C',str(ROOT),'-c','user.name=Release preparation','-c','user.email=release-preparation@localhost','commit','-m','Prepare VDMODS release repository')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pasta',type=Path,required=True)
    parser.add_argument('--validar',action='store_true')
    parser.add_argument('--criar-repositorio',action='store_true')
    parser.add_argument('--tag')
    args=parser.parse_args()
    manifest,assets=validate(args.pasta)
    if args.validar:
        print('Pacote VDMODS válido. Destino: '+CONFIG['repository']);return
    if not shutil.which('gh') or not shutil.which('git'):raise RuntimeError('Instale Git e GitHub CLI antes de publicar.')
    command('gh','auth','status')
    repo=CONFIG['repository']
    existing=command('gh','repo','view',repo,'--json','visibility,nameWithOwner,defaultBranchRef',check=False)
    if existing.returncode:
        if not args.criar_repositorio:raise RuntimeError('Repositório não disponível. Confira o acesso ou use --criar-repositorio para criar o destino configurado.')
        seed_local_repository()
        command('gh','repo','create',repo,'--public','--source',str(ROOT),'--remote','origin','--push',
            '--description','Atualizações automáticas do VDMODS')
    else:
        information=json.loads(existing.stdout)
        if information['visibility']!='PUBLIC':raise RuntimeError('O repositório precisa ser público para clientes sem token GitHub.')
        if information.get('defaultBranchRef') is None:raise RuntimeError('O repositório está vazio. Envie o commit inicial antes de publicar releases.')
    tag=args.tag or ('v'+manifest['version']+'-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S'))
    release=command('gh','release','view',tag,'--repo',repo,'--json','isDraft,isPrerelease,assets',check=False)
    if release.returncode==0 and not json.loads(release.stdout)['isDraft']:
        raise RuntimeError('Essa tag já foi publicada. Escolha outra; nenhuma release estável será sobrescrita.')
    if release.returncode:
        notes=args.pasta/'NOTAS.md'
        if not notes.is_file():raise RuntimeError('Adicione NOTAS.md à pasta dos anexos antes de publicar.')
        command('gh','release','create',tag,'--repo',repo,'--draft','--title','VDMODS '+manifest['version'],
            '--notes-file',str(notes))
    command('gh','release','upload',tag,*[str(path) for path in assets],'--repo',repo,'--clobber')
    uploaded=json.loads(command('gh','release','view',tag,'--repo',repo,'--json','assets').stdout)
    if not {path.name for path in assets}.issubset({entry['name'] for entry in uploaded['assets']}):
        raise RuntimeError('Há anexos ausentes. A release continuará como rascunho.')
    command('gh','release','edit',tag,'--repo',repo,'--draft=false','--prerelease=false','--latest')
    print('Publicado: https://github.com/'+repo+'/releases/tag/'+tag)


if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,OSError,KeyError,zipfile.BadZipFile) as error:raise SystemExit(str(error))
