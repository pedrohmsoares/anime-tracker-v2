# 🎌 Visual Anime Tracker

A highly customizable, visually driven web application designed to track anime progress at a granular level. Unlike standard trackers that only count episodes, this application allows users to organize animes by **Sagas** and **Arcs**, write specific reviews for each story section, and automatically fetch official metadata from the AniList API.

## 🤖 The Architecture & AI Collaboration

This project heavily utilizes Artificial Intelligence in its development lifecycle. 

I acted as the **Systems Architect and Orchestrator** for this application—defining the core logic, designing the UX/UI flow, mapping out the database schema, and determining feature requirements. The actual code generation, refactoring, and API integrations were executed using **Google's Gemini** as my primary AI development assistant. 

Through iterative prompt engineering and architectural direction, we built a production-ready application that seamlessly blends a local Python/Streamlit environment with cloud databases and external GraphQL APIs.

## ✨ Key Features

*   **Granular Story Tracking:** Break down long-running shows (like *One Piece* or *Black Clover*) into Sagas and Arcs for precise tracking.
*   **GraphQL API Integration:** Automatically fetches high-quality cover images, studio info, directors, community scores, and release schedules directly from the **AniList API**.
*   **Dynamic Rating System:** Rate individual Arcs based on Story, Animation, Characters, Worldbuilding, Direction, and Enjoyment. The app calculates real-time averages and renders dynamic floating badges on the gallery UI.
*   **Cloud Database:** Fully integrated with **Google Cloud Firestore (Firebase)** for real-time read/write operations, ensuring data is permanently saved and accessible across devices.
*   **Inline Editing (UX Focused):** Utilizes Streamlit Popovers for quick, inline status updates, date logging, and image replacements directly from the Overview Gallery—no need to navigate to separate edit screens.
*   **Visual Status Badges:** Automatically calculates your watch status (Planning, Watching, Completed) based on your current episode versus the total episode count.

## 🛠️ Tech Stack

*   **Frontend & UI Framework:** [Streamlit](https://streamlit.io/) (Python)
*   **Backend / Database:** Google Cloud Firestore (Firebase)
*   **External API:** AniList GraphQL API
*   **Languages & Libraries:** Python 3, `requests`, `google-cloud-firestore`, `datetime`, `json`

## 🚀 Installation & Setup

### 1. Clone the repository
```bash
git clone [https://github.com/yourusername/anime-tracker-v2.git](https://github.com/yourusername/anime-tracker-v2.git)
cd anime-tracker-v2
