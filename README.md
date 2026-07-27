# ProcDocOrganizer

Plataforma desktop extensível para organização documental e construção de
conhecimento a partir de evidências.

## Plataforma

O Platform Host 1.0 oferece lifecycle, sessões, descoberta automática de
Applications e materialização de contribuições declarativas. O pacote público
`platform_sdk` permite que uma Application registre menus, ações, views,
toolbars e dashboard sem importar Qt nem modificar o Host.

As Applications atualmente disponíveis são:

- **RSC**, preservada e compatível com a evolução da plataforma;
- **Asset Audit**, aplicação de referência que valida isolamento, discovery,
  lifecycle e Presentation SDK.

O motor documental compartilhado mantém importação, processamento de PDF, OCR
seletivo, persistência, indexação e pesquisa. Cada Application mantém seu
próprio domínio e consome apenas os contratos públicos da plataforma.

## Estado da release

A Release 1.2 encerra a fase de construção da plataforma. A arquitetura
estabilizada está documentada em
`docs/ARCHITECTURE_BASELINE_1_1.md`, e a declaração histórica do Platform Host
1.0 está em `docs/HOST_1_0_RELEASE.md`.

O próximo ciclo de desenvolvimento funcional será dedicado ao domínio RSC.
