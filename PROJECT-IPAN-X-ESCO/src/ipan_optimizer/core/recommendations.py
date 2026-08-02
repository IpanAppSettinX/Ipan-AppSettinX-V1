from __future__ import annotations

from ipan_optimizer.domain.models import (
    ApplicabilityState,
    CapabilityState,
    EvidenceLevel,
    MachineCapabilityVector,
    Recommendation,
    RiskLevel,
)


def build_recommendations(vector: MachineCapabilityVector) -> list[Recommendation]:
    recommendations: list[Recommendation] = []
    webview = vector.capabilities.get("webview2.runtime")
    if webview and webview.state is CapabilityState.UNAVAILABLE:
        recommendations.append(
            Recommendation(
                recommendation_id="rec-webview2",
                rule_id="diagnostic.webview2",
                title="Pasang WebView2 Runtime",
                reason="Runtime WebView2 belum terdeteksi.",
                risk=RiskLevel.SAFE,
                evidence_level=EvidenceLevel.VENDOR_DOCUMENTED,
                applicability=ApplicabilityState.UNAVAILABLE,
                limitation="Instalasi memerlukan persetujuan dan installer resmi.",
            )
        )
    recommendations.extend(
        [
            Recommendation(
                recommendation_id="rec-game-mode",
                rule_id="windows.game_mode",
                title="Tinjau Mode Game",
                reason="Periksa pengaturan Mode Game untuk sesi bermain.",
                risk=RiskLevel.SAFE,
                evidence_level=EvidenceLevel.VENDOR_DOCUMENTED,
                applicability=ApplicabilityState.SUPPORTED,
                limitation="Tidak menjamin peningkatan FPS pada setiap game.",
            ),
            Recommendation(
                recommendation_id="rec-storage",
                rule_id="diagnostic.storage",
                title="Tinjau ruang penyimpanan",
                reason="Ruang kosong dan aktivitas disk memengaruhi loading serta update.",
                risk=RiskLevel.SAFE,
                evidence_level=EvidenceLevel.DIAGNOSTIC_HEURISTIC,
                applicability=ApplicabilityState.SUPPORTED,
                limitation="Analisis ini tidak menghapus file secara otomatis.",
            ),
        ]
    )
    return recommendations
