// Copyright 2019, Institute for Artificial Intelligence - University of Bremen

#include "StaticSegmentationSceneProxy.h"

FStaticSegmentationSceneProxy::FStaticSegmentationSceneProxy(
    UStaticMeshComponent* Component,
    bool bForceLODsShareStaticLighting,
    UMaterialInterface* SegmentationMID)
    : FStaticMeshSceneProxy(Component, bForceLODsShareStaticLighting)
{
    bVerifyUsedMaterials = false;
    bCastShadow = false;

#if (ENGINE_MINOR_VERSION >= 22)
    MaterialRenderProxy = SegmentationMID->GetRenderProxy();
#else
    MaterialRenderProxy = SegmentationMID->GetRenderProxy(false, false);
#endif

    MaterialRelevance = SegmentationMID->GetRelevance(GetScene().GetFeatureLevel());
}

FPrimitiveViewRelevance FStaticSegmentationSceneProxy::GetViewRelevance(const FSceneView* View) const
{
    FPrimitiveViewRelevance ViewRelevance;

    // Only render when materials are enabled (used for segmentation)
    ViewRelevance.bDrawRelevance = View->Family->EngineShowFlags.Materials;
    ViewRelevance.bOpaque = true;
    ViewRelevance.bNormalTranslucency = true;
    ViewRelevance.bRenderInMainPass = true;

    return ViewRelevance;
}

void FStaticSegmentationSceneProxy::GetDynamicMeshElements(
    const TArray<const FSceneView*>& Views,
    const FSceneViewFamily& ViewFamily,
    uint32 VisibilityMap,
    FMeshElementCollector& Collector) const
{
    const int32 NumLODs = LODs.Num();

    for (int32 ViewIndex = 0; ViewIndex < Views.Num(); ++ViewIndex)
    {
        if (!(VisibilityMap & (1 << ViewIndex)))
        {
            continue;
        }

        for (int32 LODIndex = 0; LODIndex < NumLODs; ++LODIndex)
        {
            const FLODInfo& LODInfo = LODs[LODIndex];
            const int32 NumSections = LODInfo.Sections.Num();

            for (int32 SectionIndex = 0; SectionIndex < NumSections; ++SectionIndex)
            {
                FMeshBatch MeshBatch;
                if (FStaticMeshSceneProxy::GetMeshElement(
                        LODIndex,
                        SectionIndex,
                        SectionIndex,
                        SDPG_World, // Scene Depth Priority Group
    #if (ENGINE_MINOR_VERSION >= 22)
                        false,      // bUseSelectionOutline
    #else
                        false, false, // bUseSelectedMaterial, bUseHoveredMaterial
    #endif
                        false,      // bAllowPreCulledIndices
                        MeshBatch))
                {
                    // ✅ Override the material with the segmentation MID
                    MeshBatch.MaterialRenderProxy = MaterialRenderProxy;
                    MeshBatch.CastShadow = false;
                    MeshBatch.bUseWireframeSelectionColoring = false;

                    Collector.AddMesh(ViewIndex, MeshBatch);
                }
            }
        }
    }
}
