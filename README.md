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

## 🏗️ Architecture en 3 Phases

```text
DevCorp-FedSLM/
├── 1_centralized_finetuning/   # Phase 1 : Fine-tuning QLoRA (Unsloth) sur 28 467 flashcards (Dataset DiSCo)
├── 2_federated_simulation/     # Phase 2 : Simulation Cloud (Flower + Ray, 10 clients virtuels Non-I.I.D., FedProx)
├── 3_edge_raspberry_pi/        # Phase 3 : Déploiement physique sur cluster Raspberry Pi 4 (FedAvg, Float32 natif)
└── docs/                       # Rapport de recherche complet et support de présentation