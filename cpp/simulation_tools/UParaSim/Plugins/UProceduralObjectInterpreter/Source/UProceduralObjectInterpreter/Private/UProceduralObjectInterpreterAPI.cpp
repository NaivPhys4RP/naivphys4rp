#include "UProceduralObjectInterpreterAPI.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetToolsModule.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Factories/TextureFactory.h"
#include "UObject/Package.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Materials/MaterialInstanceConstant.h"
#include "PhysicalMaterials/PhysicalMaterial.h"
#include "PhysicsEngine/BodySetup.h"
#include "Components/StaticMeshComponent.h"
#include "PhysicsEngine/AggregateGeom.h"

// Added for Physics Asset manipulation
#include "PhysicsEngine/PhysicsAsset.h"

// RawMesh support for building Static Meshes
#include "RawMesh.h"

AProceduralObjectInterpreterAPI::AProceduralObjectInterpreterAPI()
{
    PrimaryActorTick.bCanEverTick = true;
}

void AProceduralObjectInterpreterAPI::BeginPlay()
{
    Super::BeginPlay();
}

void AProceduralObjectInterpreterAPI::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
}

/**
 * Programmatically generates convex collision and builds the Static Mesh.
 */
void AProceduralObjectInterpreterAPI::Internal_GenerateCollision(UStaticMesh* StaticMesh, const TArray<FVector>& Vertices)
{
    if (!StaticMesh) return;

    if (!StaticMesh->GetBodySetup())
    {
        StaticMesh->CreateBodySetup();
    }

    UBodySetup* BodySetup = StaticMesh->GetBodySetup();
    BodySetup->Modify();

    BodySetup->AggGeom.ConvexElems.Empty();

    FKConvexElem ConvexElem;
    ConvexElem.VertexData = Vertices;
    ConvexElem.UpdateElemBox();

    BodySetup->AggGeom.ConvexElems.Add(ConvexElem);

    BodySetup->CollisionTraceFlag = CTF_UseDefault;
    BodySetup->bMeshCollideAll = true;

    BodySetup->InvalidatePhysicsData();
    BodySetup->CreatePhysicsMeshes();
}

/**
 * Spawns a standard Static Mesh Actor with Physical Material Overrides.
 */
AActor* AProceduralObjectInterpreterAPI::SpawnStaticActor(UStaticMesh* MeshAsset, UPhysicalMaterial* PhysMat, FVector Location)
{
    if (!MeshAsset || !GetWorld()) return nullptr;

    FActorSpawnParameters SpawnParams;
    AActor* NewActor = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), Location, FRotator::ZeroRotator, SpawnParams);

    if (NewActor)
    {
        UStaticMeshComponent* SMC = NewObject<UStaticMeshComponent>(NewActor);
        SMC->SetStaticMesh(MeshAsset);

        if (PhysMat)
        {
            SMC->SetPhysMaterialOverride(PhysMat);
        }

        NewActor->SetRootComponent(SMC);
        SMC->RegisterComponent();
        SMC->SetSimulatePhysics(true);
    }

    return NewActor;
}

/**
 * Spawns a Destructible Actor.
 */
AMyDestructibleActor* AProceduralObjectInterpreterAPI::SpawnDestructibleActor(
    UDestructibleMesh* DMAsset,
    UPhysicalMaterial* PhysMat,
    FVector Location)
{
    if (!DMAsset || !GetWorld()) return nullptr;

    AMyDestructibleActor* NewActor = GetWorld()->SpawnActor<AMyDestructibleActor>(Location, FRotator::ZeroRotator);
    if (!NewActor) return nullptr;

    NewActor->DestructibleComp->SetDestructibleMesh(DMAsset);
    if (PhysMat) NewActor->DestructibleComp->SetPhysMaterialOverride(PhysMat);
    NewActor->DestructibleComp->WakeAllRigidBodies();

    return NewActor;
}

/**
 * The Master Import Pipeline.
 */
FGeneratedAssets AProceduralObjectInterpreterAPI::ImportFromFiles(const FString& ObjPath, const FString& TexturePath, const FString& DestinationPath)
{
    FGeneratedAssets Results;

    TArray<FVector> Positions;
    TArray<int32> Indices;
    TArray<FVector> Normals;
    TArray<FVector2D> UVs;
    TArray<int32> FaceMaterialIndices;
    TArray<FString> MaterialSlotNames;

    if (!FOBJImporter::LoadOBJ(ObjPath, Positions, Indices, Normals, UVs, FaceMaterialIndices, MaterialSlotNames))
    {
        return Results;
    }

    FString AssetBaseName = FPaths::GetBaseFilename(ObjPath);

    // Call matches the updated signature in the .h
    Results.StaticMesh = GenerateAndBuildStaticMesh(
        AssetBaseName + TEXT("_SM"),
        DestinationPath,
        Positions,
        Indices,
        UVs,
        Normals,
        FaceMaterialIndices,
        MaterialSlotNames
    );

    UTexture2D* Texture = CreateTextureFromFile(TexturePath, DestinationPath, AssetBaseName + TEXT("_Tex"));
    if (Results.StaticMesh)
    {
        for (int32 i = 0; i < MaterialSlotNames.Num(); ++i)
        {
            FString MatInstanceName = AssetBaseName + TEXT("_Mat_") + MaterialSlotNames[i];
            UMaterialInterface* Mat = FMaterialGenerator::CreateMaterialFromTexture(
                Texture,
                DestinationPath,
                MatInstanceName,
                TEXT("/Game/Materials/M_MasterProcedural")
            );

            if (Mat)
            {
                Results.StaticMesh->SetMaterial(i, Mat);
                if (i == 0) Results.Material = Mat;
            }
        }
    }

    float Density = 1.0f, Friction = 0.6f, Restitution = 0.1f;
    float Fragility = 0.5f, FragilityRate = 0.1f;
    FString MtlPath = FPaths::ChangeExtension(ObjPath, TEXT("mtl"));
    if (FPaths::FileExists(MtlPath))
    {
        FOBJImporter::ParseMTLMetadata(MtlPath, Density, Friction, Restitution, Fragility, FragilityRate);
    }

    Results.PhysicalMaterial = FPhysicalMaterialGenerator::CreatePhysicalMaterial(
        DestinationPath,
        AssetBaseName + TEXT("_Phys"),
        Friction,
        Restitution,
        Density
    );

    if (Results.StaticMesh && Results.PhysicalMaterial)
    {
        if (UBodySetup* BS = Results.StaticMesh->GetBodySetup())
        {
            BS->PhysMaterial = Results.PhysicalMaterial;
            BS->InvalidatePhysicsData();
            BS->CreatePhysicsMeshes();
        }
        Results.StaticMesh->PostEditChange();
    }

    if (Results.StaticMesh)
    {
        float ComputedThreshold = (500.0f * Density) * (1.0f - FMath::Clamp(Fragility, 0.0f, 0.95f));
        Results.DestructibleMesh = FProceduralDestroyer::CreateDestructibleFromStaticMesh(
            Results.StaticMesh,
            DestinationPath,
            AssetBaseName + TEXT("_DM"),
            ComputedThreshold,
            FragilityRate,
            Results.PhysicalMaterial
        );
    }


    // 🔹 Spawn the destructible actor immediately in the world
        if (Results.DestructibleMesh && Results.PhysicalMaterial && GetWorld())
        {
            FVector SpawnLocation(0.f, 0.f, 300.f); // example location, can be customized
            AMyDestructibleActor* DMActor = SpawnDestructibleActor(Results.DestructibleMesh, Results.PhysicalMaterial, SpawnLocation);

            if (DMActor)
            {
                UE_LOG(LogTemp, Warning, TEXT("Destructible Actor spawned at %s"), *SpawnLocation.ToString());
            }
        }

    return Results;
}

/**
 * Static Mesh Builder using the RawMesh pipeline.
 * Cleanly matches .h: AssetName, PackagePath, Positions, Indices, UVs, Normals...
 */
UStaticMesh* AProceduralObjectInterpreterAPI::GenerateAndBuildStaticMesh(
    const FString& AssetName,
    const FString& PackagePath,
    const TArray<FVector>& Positions,
    const TArray<int32>& Indices,
    const TArray<FVector2D>& UVs,
    const TArray<FVector>& Normals,
    const TArray<int32>& FaceMaterialIndices,
    const TArray<FString>& MaterialSlotNames)
{
#if WITH_EDITOR
    if (Positions.Num() == 0 || Indices.Num() == 0) return nullptr;

    FString PackageName = PackagePath + TEXT("/") + AssetName;
    UPackage* Package = CreatePackage(*PackageName);
    UStaticMesh* StaticMesh = NewObject<UStaticMesh>(Package, *AssetName, RF_Public | RF_Standalone);

    // --- RAW MESH SETUP ---
    FRawMesh RawMesh;
    RawMesh.VertexPositions = Positions;

    int32 TriangleCount = Indices.Num() / 3;

    // Reserve arrays
    RawMesh.WedgeIndices.SetNum(Indices.Num());
    RawMesh.WedgeTangentZ.SetNum(Indices.Num());
    RawMesh.WedgeTexCoords[0].SetNum(Indices.Num());
    RawMesh.WedgeColors.SetNum(Indices.Num());
    RawMesh.FaceMaterialIndices.SetNum(TriangleCount);
    RawMesh.FaceSmoothingMasks.SetNum(TriangleCount);

    // Fill wedges per triangle corner
    for (int32 Tri = 0; Tri < TriangleCount; ++Tri)
    {
        for (int32 Corner = 0; Corner < 3; ++Corner)
        {
            int32 WedgeIndex = Tri * 3 + Corner;
            int32 VertexIndex = Indices[WedgeIndex];

            RawMesh.WedgeIndices[WedgeIndex] = VertexIndex;
            RawMesh.WedgeTangentZ[WedgeIndex] = Normals.IsValidIndex(WedgeIndex) ? Normals[WedgeIndex] : FVector(0,0,1);
            RawMesh.WedgeTexCoords[0][WedgeIndex] = UVs.IsValidIndex(WedgeIndex) ? UVs[WedgeIndex] : FVector2D::ZeroVector;
            RawMesh.WedgeColors[WedgeIndex] = FColor::White;
        }

        // Assign material index per triangle
        RawMesh.FaceMaterialIndices[Tri] = FaceMaterialIndices.IsValidIndex(Tri) ? FaceMaterialIndices[Tri] : 0;
        RawMesh.FaceSmoothingMasks[Tri] = 0xFFFFFFFF; // flat shading for now
    }

    // --- ADD MATERIAL SLOTS ---
    for (const FString& SlotName : MaterialSlotNames)
    {
        FStaticMaterial NewMaterial;
        NewMaterial.MaterialInterface = nullptr;
        NewMaterial.ImportedMaterialSlotName = FName(*SlotName);
        StaticMesh->StaticMaterials.Add(NewMaterial);
    }

    // --- SOURCE MODEL ---
    FStaticMeshSourceModel& SrcModel = StaticMesh->AddSourceModel();
    SrcModel.BuildSettings.bRecomputeNormals = false;
    SrcModel.BuildSettings.bRecomputeTangents = true;
    SrcModel.RawMeshBulkData->SaveRawMesh(RawMesh);

    // Build mesh
    StaticMesh->Build(false);
    StaticMesh->InitResources();

    // --- COLLISION ---
    Internal_GenerateCollision(StaticMesh, Positions);

    // Notify editor
    StaticMesh->PostEditChange();
    StaticMesh->MarkPackageDirty();
    FAssetRegistryModule::AssetCreated(StaticMesh);

    return StaticMesh;
#endif
    return nullptr;
}

/**
 * Binary texture importer.
 */
UTexture2D* AProceduralObjectInterpreterAPI::CreateTextureFromFile(const FString& FilePath, const FString& PackagePath, const FString& AssetName)
{
#if WITH_EDITOR
    TArray<uint8> RawFileData;
    if (!FPaths::FileExists(FilePath) || !FFileHelper::LoadFileToArray(RawFileData, *FilePath)) return nullptr;

    FString PackageName = PackagePath + TEXT("/") + AssetName;
    UPackage* Package = CreatePackage(*PackageName);

    UTextureFactory* TextureFact = NewObject<UTextureFactory>();
    TextureFact->AddToRoot();

    const uint8* BufferPtr = RawFileData.GetData();
    UTexture2D* Texture = Cast<UTexture2D>(TextureFact->FactoryCreateBinary(
        UTexture2D::StaticClass(), Package, *AssetName, RF_Public | RF_Standalone, nullptr,
        *FPaths::GetExtension(FilePath), BufferPtr, BufferPtr + RawFileData.Num(), GWarn));

    if (Texture)
    {
        Texture->MarkPackageDirty();
        FAssetRegistryModule::AssetCreated(Texture);
    }

    TextureFact->RemoveFromRoot();
    return Texture;
#endif
    return nullptr;
}

/**
 * FOBJImporter Implementation.
 */
bool FOBJImporter::LoadOBJ(const FString& ObjPath, TArray<FVector>& OutPositions, TArray<int32>& OutIndices, TArray<FVector>& OutNormals, TArray<FVector2D>& OutUVs, TArray<int32>& OutFaceMaterialIndices, TArray<FString>& OutMaterialNames)
{
    FString FileContents;
    if (!FFileHelper::LoadFileToString(FileContents, *ObjPath)) return false;

    TArray<FString> Lines;
    FileContents.ParseIntoArrayLines(Lines);

    TArray<FVector> TmpPositions;
    TArray<FVector> TmpNormals;
    TArray<FVector2D> TmpUVs;

    int32 CurrentMaterialIndex = 0;
    TMap<FString, int32> MaterialNameToIndex;

    for (const FString& Line : Lines)
    {
        FString Trim = Line.TrimStartAndEnd();
        if (Trim.StartsWith("#") || Trim.Len() == 0) continue;

        TArray<FString> Tokens;
        Trim.ParseIntoArrayWS(Tokens);
        if (Tokens.Num() == 0) continue;

        if (Tokens[0] == "usemtl" && Tokens.Num() >= 2)
        {
            FString MtlName = Tokens[1];
            if (!MaterialNameToIndex.Contains(MtlName))
            {
                int32 NewIdx = OutMaterialNames.Add(MtlName);
                MaterialNameToIndex.Add(MtlName, NewIdx);
            }
            CurrentMaterialIndex = MaterialNameToIndex[MtlName];
        }
        else if (Tokens[0] == "v" && Tokens.Num() >= 4)
        {
            TmpPositions.Add(FVector(FCString::Atod(*Tokens[1]), FCString::Atod(*Tokens[2]), FCString::Atod(*Tokens[3])));
        }
        else if (Tokens[0] == "vn" && Tokens.Num() >= 4)
        {
            TmpNormals.Add(FVector(FCString::Atod(*Tokens[1]), FCString::Atod(*Tokens[2]), FCString::Atod(*Tokens[3])));
        }
        else if (Tokens[0] == "vt" && Tokens.Num() >= 3)
        {
            TmpUVs.Add(FVector2D(FCString::Atod(*Tokens[1]), 1.0f - FCString::Atod(*Tokens[2])));
        }
        else if (Tokens[0] == "f" && Tokens.Num() >= 4)
        {
            TArray<int32> FaceIndices;
            for (int32 i = 1; i < Tokens.Num(); ++i)
            {
                TArray<FString> Parts;
                Tokens[i].ParseIntoArray(Parts, TEXT("/"), false);

                int32 pIdx = Parts.Num() > 0 ? FCString::Atoi(*Parts[0]) - 1 : -1;
                int32 tIdx = Parts.Num() > 1 ? FCString::Atoi(*Parts[1]) - 1 : -1;
                int32 nIdx = Parts.Num() > 2 ? FCString::Atoi(*Parts[2]) - 1 : -1;

                int32 PosIdx = OutPositions.Add(TmpPositions.IsValidIndex(pIdx) ? TmpPositions[pIdx] : FVector::ZeroVector);
                OutNormals.Add(TmpNormals.IsValidIndex(nIdx) ? TmpNormals[nIdx] : FVector(0,0,1));
                OutUVs.Add(TmpUVs.IsValidIndex(tIdx) ? TmpUVs[tIdx] : FVector2D::ZeroVector);

                FaceIndices.Add(PosIdx);
            }

            for (int32 k = 1; k + 1 < FaceIndices.Num(); ++k)
            {
                OutIndices.Add(FaceIndices[0]);
                OutIndices.Add(FaceIndices[k]);
                OutIndices.Add(FaceIndices[k + 1]);
                // This correctly adds the material index for EVERY triangle created from a quad
                OutFaceMaterialIndices.Add(CurrentMaterialIndex);
            }
        }
    }
    if (OutMaterialNames.Num() == 0) OutMaterialNames.Add(TEXT("DefaultMaterial"));
    return OutPositions.Num() > 0;
}

void FOBJImporter::ParseMTLMetadata(const FString& MtlPath, float& OutDensity, float& OutFriction, float& OutRestitution, float& OutFragility, float& OutFragilityRate)
{
    FString FileContents;
    if (!FFileHelper::LoadFileToString(FileContents, *MtlPath)) return;

    TArray<FString> Lines;
    FileContents.ParseIntoArrayLines(Lines);

    for (const FString& Line : Lines)
    {
        TArray<FString> Tokens;
        Line.TrimStartAndEnd().ParseIntoArrayWS(Tokens);
        if (Tokens.Num() < 2) continue;

        if (Tokens[0] == "X_density") OutDensity = FCString::Atof(*Tokens[1]);
        else if (Tokens[0] == "X_friction") OutFriction = FCString::Atof(*Tokens[1]);
        else if (Tokens[0] == "X_restitution") OutRestitution = FCString::Atof(*Tokens[1]);
        else if (Tokens[0] == "X_absolute_fragility") OutFragility = FCString::Atof(*Tokens[1]);
        else if (Tokens[0] == "X_fragility_rate") OutFragilityRate = FCString::Atof(*Tokens[1]);
    }
}

UMaterialInterface* FMaterialGenerator::CreateMaterialFromTexture(UTexture2D* Texture, const FString& PackagePath, const FString& MaterialName, const FString& BaseMaterialPath)
{
#if WITH_EDITOR
    FString PackageName = PackagePath + TEXT("/") + MaterialName;
    UPackage* Package = CreatePackage(*PackageName);
    UMaterialInterface* ParentMat = Cast<UMaterialInterface>(StaticLoadObject(UMaterialInterface::StaticClass(), nullptr, *BaseMaterialPath));
    if (!ParentMat) return nullptr;

    UMaterialInstanceConstant* MatInst = NewObject<UMaterialInstanceConstant>(Package, *MaterialName, RF_Public | RF_Standalone);
    MatInst->SetParentEditorOnly(ParentMat);
    if (Texture) MatInst->SetTextureParameterValueEditorOnly(FMaterialParameterInfo(TEXT("BaseTexture")), Texture);

    MatInst->PostEditChange();
    FAssetRegistryModule::AssetCreated(MatInst);
    return MatInst;
#endif
    return nullptr;
}

UPhysicalMaterial* FPhysicalMaterialGenerator::CreatePhysicalMaterial(const FString& PackagePath, const FString& PhysName, float Friction, float Restitution, float Density)
{
#if WITH_EDITOR
    FString PackageName = PackagePath + TEXT("/") + PhysName;
    UPackage* Package = CreatePackage(*PackageName);
    UPhysicalMaterial* Phys = NewObject<UPhysicalMaterial>(Package, *PhysName, RF_Public | RF_Standalone);
    Phys->Friction = Friction;
    Phys->Restitution = Restitution;
    Phys->Density = Density;
    Phys->MarkPackageDirty();
    FAssetRegistryModule::AssetCreated(Phys);
    return Phys;
#endif
    return nullptr;
}

/**
 * Destructible Mesh Generator.
 */
UDestructibleMesh* FProceduralDestroyer::CreateDestructibleFromStaticMesh(UStaticMesh* StaticMesh, const FString& PackagePath, const FString& DMName, float Threshold, float FragilityRate, UPhysicalMaterial* PhysMat)
{
#if WITH_EDITOR
    if (!StaticMesh) return nullptr;

    FString PackageName = PackagePath + TEXT("/") + DMName;
    UPackage* Package = CreatePackage(*PackageName);
    UDestructibleMesh* DM = NewObject<UDestructibleMesh>(Package, *DMName, RF_Public | RF_Standalone);

    if (DM)
    {
        DM->SourceStaticMesh = StaticMesh;
        DM->BuildFromStaticMesh(*StaticMesh);

        FDestructibleParameters& Params = DM->DefaultDestructibleParameters;
        Params.DamageParameters.ImpactDamage = FragilityRate;
        Params.DamageParameters.bEnableImpactDamage = (FragilityRate > 0.0f);
        Params.Flags.bAccumulateDamage = true;
        Params.Flags.bWorldSupport = true;
        Params.DamageParameters.DamageThreshold = Threshold;
        Params.SpecialHierarchyDepths.SupportDepth = 1;

        if (PhysMat && DM->GetPhysicsAsset())
        {
            UPhysicsAsset* PhysAsset = DM->GetPhysicsAsset();
            for (UBodySetup* BodySetup : PhysAsset->SkeletalBodySetups)
            {
                if (BodySetup)
                {
                    BodySetup->Modify();
                    BodySetup->PhysMaterial = PhysMat;
                    BodySetup->InvalidatePhysicsData();
                    BodySetup->CreatePhysicsMeshes();
                }
            }
            PhysAsset->MarkPackageDirty();
        }

        DM->MarkPackageDirty();
        FAssetRegistryModule::AssetCreated(DM);
        return DM;
    }
#endif
    return nullptr;
}


