# 🛡️ DevCorp-FedSLM : Apprentissage Fédéré pour la Génération et l'Audit de Code Sécurisé sur l'Edge

**Déploiement de Petits Modèles de Langage (SLM) sur dispositifs à ressources contraintes (Raspberry Pi 4) pour l'assistance au développement sécurisé et confidentiel.**

> *Projet de recherche & d'ingénierie réalisé à l'Institut National des Postes et Télécommunications (INPT).*

---

## 🎯 Contexte et Problématique

Les grands modèles de langage (LLM) commerciaux génèrent fréquemment du code comportant des vulnérabilités critiques (injections SQL, failles CWE). Par ailleurs, les organisations sensibles (**Banques, Hôpitaux, Défense**) ne peuvent pas envoyer leur code source propriétaire vers des API Cloud tierces en raison des risques de fuite de propriété intellectuelle et des contraintes réglementaires (**RGPD, HIPAA**).

**Notre solution (Architecture DevCorp) :**
1. **Unification Génération + Audit :** Spécialiser un Petit Modèle de Langage (**Qwen2.5-Coder-0.5B-Instruct**) capable à la fois de **générer du code sécurisé** et d'**auditer du code vulnérable** avec explication du raisonnement.
2. **Apprentissage Fédéré (Federated Learning) :** Entraîner collaborativement le modèle entre plusieurs entités (Équipe Banque, Équipe Santé) via **Flower** (`FedProx` / `FedAvg`) en n'échangeant que les poids des adaptateurs **LoRA**, sans jamais partager les données brutes.
3. **Souveraineté sur l'Edge :** Déployer et entraîner le modèle directement sur un cluster physique de **Raspberry Pi 4 (CPU ARM Cortex-A72, 4 Go RAM)**.

---

## 🏗️ Architecture du Projet

```text
DevCorp-FedSLM/
├── 1_centralized_finetuning/   # Phase 1 : Fine-tuning QLoRA (Unsloth) sur 28 467 flashcards (Dataset DiSCo)
├── 2_federated_simulation/     # Phase 2 : Simulation Cloud (Flower + Ray, 10 clients virtuels Non-I.I.D., FedProx)
├── 3_edge_raspberry_pi/        # Phase 3 : Déploiement physique sur cluster Raspberry Pi 4 (FedAvg, Float32 natif)
└── docs/                       # Rapport de recherche complet et support de présentation
```

### Phase 1 : Ingénierie des Données & Fine-Tuning Centralisé
* **Modèle de base :** `Qwen2.5-Coder-0.5B-Instruct` (490M paramètres, quantification 4-bit via **Unsloth**).
* **Dataset Unifié :** Transformation des 9 489 lignes du corpus `StonyBrookNLP/DiSCo` en **28 467 flashcards conversationnelles ChatML** couvrant 3 tâches :
  1. *Développeur (Génération)* : Produire du code Python sécurisé (requêtes SQL paramétrées, gestion des ressources).
  2. *Auditeur (Détection positive)* : Identifier la faille CWE et expliquer le vecteur d'attaque (`VULNERABLE. Reasoning: ...`).
  3. *Auditeur (Détection négative)* : Valider le code sain (`SECURE.`).
* **Adaptation LoRA :** `r = 16`, `lora_alpha = 16` ciblant les modules d'attention et MLP (**1,75 %** de paramètres entraînés, soit 8,8M).

### Phase 2 : Simulation Fédérée Non-I.I.D. (Cloud)
* **Orchestration :** **Flower** + moteur distribué **Ray** sur GPU Tesla T4, avec la stratégie **FedProx** ($\mu = 0.01$).
* **Moteur de partitionnement Non-I.I.D. dynamique :** 10 clients virtuels répartis selon 4 profils métiers asymétriques (*Spécialiste Génération 80/10/10*, *Analyste Vulnérabilités 10/80/10*, *Auditeur Sécurité 10/10/80*, *Généraliste 34/33/33*) avec ré-échantillonnage dynamique inter-rondes.

### Phase 3 : Déploiement Physique sur Cluster Raspberry Pi 4 (Edge)
* **Matériel :** 2 nœuds clients **Raspberry Pi 4 (4 Go RAM, ARM64)** représentant l'**Équipe Banque** (`banque_data.jsonl`) et l'**Équipe Santé** (`sante_data.jsonl`, conformité HIPAA / hachage SHA-256), connectés en Wi-Fi/TCP (port `8080`) au serveur central **DevCorp HQ**.
* **Optimisation CPU ARM :** Exécution **Float32 native** couplée au **Multiprocessing Quad-Core** (`torch.set_num_threads`) et boucle d'entraînement PyTorch allégée sur `q_proj` et `v_proj`.

---

## 📊 Résultats Expérimentaux

### 1. Performances de Génération de Code Sécurisé (Centralisé vs Fédéré Simulé)

| Métrique | Modèle Centralisé (P1) | Modèle Fédéré (P2 - 10 clients) | Interprétation |
| :--- | :---: | :---: | :--- |
| **Perplexité (PPL)** | 1,80 | **1,70** | Excellente confiance prédictive (régularisation implicite FedProx) |
| **SacreBLEU / BLEU** | **47,42** | 46,44 | Préservation de 98 % des capacités lexicales |
| **ROUGE-L** | **55,95 %** | 52,39 % | Forte cohérence des séquences générées |
| **CodeBLEU (Global)** | **49,25** | 39,27 | Solide maîtrise structurelle du code Python |
| ├─ *Syntax Match (AST)* | **58,07 %** | **58,07 %** | 100 % de préservation de la validité syntaxique (AST) |
| └─ *Dataflow Match* | **45,05 %** | **45,05 %** | 100 % de préservation des flots de données sécurisés |

### 2. Performances d'Audit Binaire (Holdout de 200 extraits inédits)
* **Modèle Centralisé :** **Accuracy : 74,0 %** | **Précision : 72,2 %** | **Rappel : 78,0 %** | **F1-Score : 75,0 %**.
* **Analyse Fédérée Non-I.I.D. (3 rondes) :** L'étude démontre que si 3 rondes suffisent à préserver 100 % de la structure syntaxique et du flot de données en génération, la frontière de décision discrète pour la classification binaire en environnement fortement non-i.i.d. nécessite un budget de communication supérieur (10 à 50 rondes).

### 3. Convergence sur Matériel Embarqué (Cluster Raspberry Pi 4)
Quatre configurations hyperparamétriques ont été évaluées sur le cluster physique (3 rondes FedAvg) :

| Configuration | `MAX_LENGTH` | `LORA_R` | Learning Rate (`LR`) | Loss Globale Finale | Accuracy Globale (Token-Level) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Setup 1 (Baseline)** | 48 | 4 | 1e-4 | 3,17 | 60,11 % |
| **Setup 2 (Contexte +)** | 64 | 4 | 2e-4 | 2,56 | 65,48 % |
| **Setup 3 (Sweet Spot)** | **1028** | **8** | **5e-2** | **1,64** | **70,94 %** |
| **Setup 4 (Stress Test)** | 2048 | 8 | 6e-2 | 2,16 | 68,60 % |

> Le **Setup 3** permet une convergence continue sur Raspberry Pi (`68,55 % -> 69,70 % -> 70,94 %`) en ~6 minutes pour 3 rondes complètes.

---

## 🚀 Installation et Utilisation

### 1. Environnement Cloud (Fine-Tuning & Simulation Flower)

```bash
pip install transformers==4.48.3 datasets trl evaluate bitsandbytes accelerate peft
pip install "unsloth[kaggle-new] @ git+https://github.com/unslothai/unsloth.git"
pip install flwr[simulation] ray codebleu
```

### 2. Déploiement sur Cluster Raspberry Pi (ARM64)

```bash
python3 -m venv fl_env
source fl_env/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers datasets peft flwr
```

**Lancement de l'entraînement fédéré réel :**
1. **Sur le serveur central (DevCorp HQ - `192.168.0.102:8080`) :**
   ```bash
   python3 3_edge_raspberry_pi/server.py
   ```
2. **Sur les Raspberry Pi (Équipe Banque & Équipe Santé) :**
   ```bash
   python3 3_edge_raspberry_pi/client.py
   ```

---

## 📄 Documentation

* 📘 **[Rapport Technique Complet (PDF)](Docs/Rapport_Federated_SLM_INPT.pdf)**
* 📊 **[Présentation du Projet (Slides PDF)](Docs/Presentation_Federated_SLM.pdf)**

---

## 👥 Auteurs & Encadrement

* **Réalisé par :** **Zakaria Bigane** & **Marwan Moujane** — Élèves ingénieurs en cybersécurité à l'INPT (Rabat).
* **Encadré par :** **Dr. Meryem Ayache** & **Dr. Douae El Achhab**.
