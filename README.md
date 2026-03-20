# HONEY_MULTISERVICE (VPS1)

Infraestructura **multi-honeypot en Docker Compose** para Ubuntu Server 24.04 LTS, orientada a captura real de ataques en internet en el **VPS1** (zona de alto riesgo).

> Alcance de este repositorio: solo despliegue de captura en VPS1. No incluye VPS2 ni correlación/SIEM.

---

## 1) Arquitectura propuesta

### Objetivo operativo
Desplegar servicios honeypot en contenedores aislados con:
- Puertos controlados y explícitos.
- Persistencia de evidencias por servicio.
- Reinicio automático.
- Endurecimiento base (mínimo privilegio, `no-new-privileges`, límites CPU/RAM).

### Topología de redes
- **`honeynet_net` (bridge, NO internal):** red de exposición lógica para servicios que reciben tráfico atacante (vía puertos publicados).
- **`log_net` (bridge, internal=true):** red interna para futuro forwarder/log-shipper y tránsito auxiliar de telemetría.
- **`mgmt_net` (bridge, internal=true):** red de administración interna (actualmente usada por `webtrap`; reservada para herramientas locales de gestión/inspección en VPS1).

> En Docker Compose, la exposición real a internet se realiza mediante `ports:` sobre la IP del host VPS.

---

## 2) Honeypots desplegados

### 2.1 Cowrie (`hp_cowrie`)
- Rol: SSH/Telnet honeypot.
- Captura: brute force, credenciales, comandos, sesiones interactivas, upload/download.
- Puertos publicados:
  - `2222 -> 2222/tcp` (SSH)
  - `2223 -> 2223/tcp` (Telnet)
- Persistencia:
  - `./data/cowrie/var`
  - `./data/cowrie/etc`
  - `./data/cowrie/logs`

### 2.2 Dionaea (`hp_dionaea`)
- Rol: captura malware/payloads y explotación de servicios emulados.
- Puertos publicados (laboratorio mínimo): `21`, `69/udp`, `80`, `135`, `445`, `1433`, `1723`, `3306`, `5060`.
- Persistencia:
  - `./data/dionaea/logs`
  - `./data/dionaea/downloads`

### 2.3 Elastic honeypot (`hp_elasticpot`)
- Requisito original: ElasticPot.
- Decisión técnica: usar **ElasticPot local** (implementación mínima en Flask dentro de `services/elasticpot`) para evitar dependencia de imágenes GHCR con pull anónimo inestable y mantener trazabilidad del código.
- Puerto publicado: `9200 -> 9200/tcp`.
- Persistencia:
  - `./data/elasticpot/logs/elasticpot.jsonl`

### 2.4 Mailoney (`hp_mailoney`)
- Rol: SMTP honeypot local (implementación propia) para no depender de imágenes remotas frágiles.
- Captura: banner SMTP, comandos, intentos de relay y payload en `DATA`.
- Puerto publicado: `25 -> 2525/tcp` (host:contenedor, para evitar privilegios root en el contenedor).
- Persistencia:
  - `./data/mailoney/logs`

### 2.5 Conpot (`hp_conpot`)
- Rol: honeypot ICS/OT local pragmático (alternativa lightweight).
- Superficie ICS publicada:
  - `102 -> 1102/tcp` (S7-like handshake)
  - `502 -> 1502/tcp` (Modbus-like respuesta)
  - `16100/udp` (SNMP-like logging)
  - `44818/tcp` (EtherNet/IP-like respuesta)
- Persistencia:
  - `./data/conpot/logs`
  - `./data/conpot/configs`

### 2.6 Web honeypot ligero (`hp_webtrap`)
- Implementación propia en Flask (`services/webtrap`).
- Rol: capturar reconocimiento web, escaneo de rutas, payloads básicos y bots.
- Respuesta: página HTML genérica para mantener interacción.
- Detección simple por patrones (SQLi/path traversal/LFI/JNDI/`wp-admin`/`.env`) y alertas separadas.
- Puertos publicados:
  - `8088 -> 8080/tcp` (HTTP)
  - `8443 -> 8443/tcp` (HTTPS adhoc self-signed)
- Persistencia:
  - `./data/webtrap/logs` (`requests.jsonl`, `alerts.jsonl`)

---

## 3) Estructura de carpetas

```text
HONEY_MULTISERVICE/
├── docker-compose.yml
├── .env.example
├── README.md
├── services/
│   ├── elasticpot/
│   │   ├── Dockerfile
│   │   ├── app.py
│   │   └── requirements.txt
│   ├── mailoney/
│   │   ├── Dockerfile
│   │   ├── app.py
│   │   └── entrypoint.sh
│   ├── conpot/
│   │   ├── Dockerfile
│   │   ├── app.py
│   │   ├── entrypoint.sh
│   │   └── config.sample.yaml
│   └── webtrap/
│       ├── Dockerfile
│       ├── app.py
│       └── requirements.txt
└── data/
    ├── cowrie/{etc,logs,var}
    ├── dionaea/{downloads,logs}
    ├── elasticpot/logs
    ├── mailoney/logs
    ├── conpot/{configs,logs}
    └── webtrap/logs
```

---

## 4) Despliegue en Ubuntu Server 24.04 LTS

## 4.1 Preparar host
```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release ufw

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

> Recomendado: cerrar sesión y volver a entrar para aplicar grupo `docker`.

## 4.2 Configurar proyecto
```bash
cp .env.example .env
# opcional: editar puertos
nano .env
```

## 4.3 Levantar stack
```bash
docker compose pull
docker compose build
docker compose up -d
```

---

## 5) Mapa de puertos (host VPS1)

- Cowrie SSH: `2222/tcp`
- Cowrie Telnet: `2223/tcp`
- Dionaea: `21/tcp`, `69/udp`, `80/tcp`, `135/tcp`, `445/tcp`, `1433/tcp`, `1723/tcp`, `3306/tcp`, `5060/tcp`
- Elastic honeypot: `9200/tcp`
- Mailoney SMTP: `25/tcp`
- Conpot ICS: `102/tcp`, `502/tcp`, `16100/udp`, `44818/tcp`
- Web honeypot: `8088/tcp`, `8443/tcp`

---

## 6) Endurecimiento y seguridad (VPS1)

1. **Mínimo privilegio en contenedores**
   - `cap_drop: [ALL]` cuando viable.
   - `security_opt: no-new-privileges:true`.
   - `read_only: true` + `tmpfs` en servicios aptos.

2. **Límites de recursos**
   - `cpus` y `mem_limit` definidos por servicio para reducir impacto de abuso.

3. **Aislamiento de red**
   - Red interna para `log_net` y `mgmt_net`.
   - Publicar solo puertos estrictamente necesarios.

4. **Persistencia selectiva**
   - Volúmenes solo para evidencia/config mínima.

5. **Control de egress recomendado (host)**
   - Política de salida restrictiva por defecto en host/iptables.
   - Permitir únicamente DNS/NTP/repositorios para operación controlada.
   - Si deseas máxima contención, aplicar reglas DOCKER-USER para bloquear salida de subredes Docker excepto destinos explícitos.

6. **Evitar pivot/bot**
   - Nunca desplegar secretos reales en VPS1.
   - Mantener host parchado.
   - No co-ubicar servicios productivos en el mismo VPS.
   - Monitorear conexiones salientes inusuales desde redes Docker.

---

## 7) Recomendación de firewall (UFW)

Ejemplo base (ajusta IP de administración):

```bash
sudo ufw default deny incoming
sudo ufw default deny outgoing

# Administración
sudo ufw allow from <TU_IP_ADMIN>/32 to any port 22 proto tcp

# Inbound honeypots
sudo ufw allow 2222/tcp
sudo ufw allow 2223/tcp
sudo ufw allow 21/tcp
sudo ufw allow 69/udp
sudo ufw allow 80/tcp
sudo ufw allow 135/tcp
sudo ufw allow 445/tcp
sudo ufw allow 1433/tcp
sudo ufw allow 1723/tcp
sudo ufw allow 3306/tcp
sudo ufw allow 5060/tcp
sudo ufw allow 9200/tcp
sudo ufw allow 25/tcp
sudo ufw allow 102/tcp
sudo ufw allow 502/tcp
sudo ufw allow 16100/udp
sudo ufw allow 44818/tcp
sudo ufw allow 8088/tcp
sudo ufw allow 8443/tcp

# Outbound mínimo sugerido (host)
sudo ufw allow out 53
sudo ufw allow out 123/udp
sudo ufw allow out 443/tcp

sudo ufw enable
sudo ufw status verbose
```

> Ajusta reglas de salida según política institucional. Si el stack requiere resolver DNS o descargar imágenes, habilítalo temporalmente durante despliegue.

---

## 8) Validación de funcionamiento

### Verificar estado de contenedores
```bash
docker compose ps
```

### Verificar puertos en escucha (host)
```bash
ss -tulpen | egrep ':2222|:2223|:21|:69|:80|:135|:445|:1433|:1723|:3306|:5060|:9200|:25|:102|:502|:16100|:44818|:8088|:8443'
```

### Smoke tests controlados (no destructivos)
```bash
# Cowrie
nc -vz <IP_VPS1> 2222
nc -vz <IP_VPS1> 2223

# Elastic honeypot
curl -i http://<IP_VPS1>:9200/

# SMTP honeypot
nc -vz <IP_VPS1> 25

# Web honeypot
curl -i http://<IP_VPS1>:8088/
curl -k -i https://<IP_VPS1>:8443/

# Reconocimiento de puertos
nmap -sV -Pn <IP_VPS1> -p 25,80,102,445,502,9200,2222,2223,8088,8443
```

### Verificar generación de logs
```bash
# Logs por servicio
ls -lah data/cowrie/logs
ls -lah data/dionaea/logs data/dionaea/downloads
ls -lah data/elasticpot/logs
ls -lah data/mailoney/logs
ls -lah data/conpot/logs
ls -lah data/webtrap/logs

# Evento webtrap
tail -n 20 data/webtrap/logs/requests.jsonl
tail -n 20 data/webtrap/logs/alerts.jsonl
```

---

## 9) Preparación para futura integración con Wazuh Agent (solo host)

Sin instalar Wazuh aquí, se deja listo el patrón de ingestión:
- Todas las evidencias quedan bajo `./data/<servicio>/logs`.
- Recomendación operativa en VPS1: montar repo en `/opt/honey_multiservice` para rutas estables.
- Posteriormente, el agente Wazuh del host podrá vigilar rutas:
  - `/opt/honey_multiservice/data/*/logs/**`

---

## 10) Notas académicas para defensa

- La arquitectura separa claramente **captura** (VPS1) de análisis futuro (VPS2).
- Se aplica un enfoque **defense-in-depth**: aislamiento por red, principio de mínimo privilegio, límites de recursos y persistencia controlada.
- Se incluye superficie IT + OT para mayor diversidad de TTPs observables.
- El diseño es reproducible y versionable mediante `docker-compose.yml` + `.env`.
