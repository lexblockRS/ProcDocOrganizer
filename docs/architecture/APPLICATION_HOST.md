# Application Host

## Objetivo

O Application Host transforma o ProcDocOrganizer em uma plataforma capaz de
descobrir, registrar e hospedar aplicações independentes. O núcleo conhece
somente contratos neutros, descriptors, registry, lifecycle e sessões. RSC é
um módulo consumidor desses contratos e não uma dependência da plataforma.

## Componentes

```text
ApplicationProvider
        ↓ discovery
ApplicationCatalog
        ↓ módulos encontrados
ApplicationRegistry
        ↓ descriptor / módulo
ApplicationRuntime
        ↓ lifecycle e sessão
ApplicationLifecycleHost
```

### ApplicationDescriptor

Metadado passivo, imutável e sem lógica de negócio:

- `application_id`;
- `display_name`;
- `version`;
- `description`;
- `icon` opcional;
- `author`;
- `services`;
- `views`;
- `commands`;
- capacidades requeridas e fornecidas;
- versão mínima da plataforma;
- schemas de projeto suportados.

Services, views, commands e capacidades são identificadores declarativos. O
descriptor não instancia objetos, executa comandos ou monta telas.

### Application e ApplicationModule

`Application` preserva o contrato legado mínimo de identidade,
compatibilidade de projeto e contribuições. `ApplicationModule` define a
fronteira modular de descriptor, preparação, criação de sessão, contribuições,
transições de lifecycle e descarte.

Ambos são Protocols neutros. Implementações concretas pertencem às aplicações.

### ApplicationRegistry

O Registry:

- registra aplicações e módulos;
- impede colisões entre IDs e aliases;
- recupera módulo, objeto ou descriptor por ID;
- lista aplicações instaladas por `list()`;
- mantém ordenação determinística pelo ID;
- valida compatibilidade de plataforma e schema.

`list()` retorna somente uma tupla de `ApplicationDescriptor`. Uma UI futura
pode apresentar aplicações instaladas sem criar sessões nem executar lógica.

### RscApplication

`RscApplication` implementa os contratos da plataforma e declara seu
descriptor. Ela é descoberta por `applications.rsc.provider`, registrada como
qualquer outro módulo e cria seus próprios componentes apenas quando o Host
solicita uma sessão.

O Host não importa `RscApplication` e não conhece Criterion, ExecutionFact,
Kernel ou NormativeCriterionCatalog.

## Ciclo de registro

```text
pacote applications
        ↓ discovery de providers
ApplicationProvider
        ↓ applications()
ApplicationCatalog
        ↓ validação e ordenação
ApplicationRegistry.register()
        ↓
registry.list() / registry.get()
```

Registro não prepara o módulo, não cria sessão e não consome contribuições.
Essas ações pertencem ao lifecycle posterior.

## Direção de dependências

```text
contracts ← core/platform_sdk ← aplicação concreta
```

A aplicação concreta pode conhecer a plataforma. A plataforma não pode
conhecer a aplicação concreta. Descriptors não podem importar lógica de
negócio.

## Extensão futura

Para adicionar uma aplicação:

1. implementar `ApplicationModule`;
2. declarar `ApplicationDescriptor`;
3. fornecer `ApplicationProvider`;
4. disponibilizar o provider sob o pacote descoberto;
5. declarar contribuições por contratos da plataforma;
6. testar ID, compatibilidade e lifecycle.

Evoluções possíveis incluem ícones resolvidos por resource provider,
localização de metadados, permissões por capacidade, ativação seletiva,
assinatura de módulos e instalação externa. Essas evoluções não devem fazer o
Host depender de domínios concretos.
