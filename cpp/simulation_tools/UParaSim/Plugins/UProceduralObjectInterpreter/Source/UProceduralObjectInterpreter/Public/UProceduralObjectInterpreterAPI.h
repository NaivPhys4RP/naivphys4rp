#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "UObject/NoExportTypes.h"
// APEX Destruction (UE 4.27)
#include "DestructibleMesh.h"
#include "DestructibleComponent.h"
#include "UProceduralObjectInterpreterAPI.generated.h"

// Forward declarations to keep header lightweight
class UDestructibleMesh;
class UTexture2D;
class UStaticMesh;
class UMaterialInterface;
class UPhysicalMaterial;



UCLASS()
class AMyDestructibleActor : public AActor
{
    GENERATED_BODY()
public:
    AMyDestructibleActor()
    {
        DestructibleComp = CreateDefaultSubobject<UDestructibleComponent>(TEXT("DestructibleComp"));
        SetRootComponent(DestructibleComp);
        DestructibleComp->SetSimulatePhysics(true);
        DestructibleComp->SetCollisionProfileName(TEXT("Destructible"));
    }

    UPROPERTY(VisibleAnywhere, BlueprintReadWrite)
    UDestructibleComponent* DestructibleComp;
};




/**
 * FGeneratedAssets
 * Container for assets produced during the procedural import process.
 */
USTRUCT(BlueprintType)
struct FGeneratedAssets
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Procedural")
    UStaticMesh* StaticMesh = nullptr;

    UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Procedural")
    UDestructibleMesh* DestructibleMesh = nullptr;

    UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Procedural")
    UMaterialInterface* Material = nullptr;

    UPROPERTY(VisibleAnywhere, BlueprintReadWrite, Category = "Procedural")
    UPhysicalMaterial* PhysicalMaterial = nullptr;
};

/** * FOBJImporter
 * Parses Wavefront .obj files and associated .mtl metadata.
 */
class FOBJImporter
{
public:
    static bool LoadOBJ(
        const FString& ObjPath,
        TArray<FVector>& OutPositions,
        TArray<int32>& OutIndices,
        TArray<FVector>& OutNormals,
        TArray<FVector2D>& OutUVs,
        TArray<int32>& OutFaceMaterialIndices,
        TArray<FString>& OutMaterialNames);

    static void ParseMTLMetadata(const FString& MtlPath, float& OutDensity, float& OutFriction, float& OutRestitution, float& OutFragility, float& OutFragilityRate);
};

/** * FMaterialGenerator
 * Creates Material Instance Constants and binds them to a Master Material.
 */
class FMaterialGenerator
{
public:
    static UMaterialInterface* CreateMaterialFromTexture(UTexture2D* Texture, const FString& PackagePath, const FString& MaterialName, const FString& BaseMaterialPath = TEXT("/Game/Materials/Base_Albedo"));
};

/** * FPhysicalMaterialGenerator
 * Generates UPhysicalMaterial assets with specific physical properties.
 */
class FPhysicalMaterialGenerator
{
public:
    static UPhysicalMaterial* CreatePhysicalMaterial(const FString& PackagePath, const FString& PhysName, float Friction = 0.6f, float Restitution = 0.1f, float Density = 1.0f);
};

/** * FProceduralDestroyer
 * APEX Destruction integration for converting meshes.
 */
class FProceduralDestroyer
{
public:
    static UDestructibleMesh* CreateDestructibleFromStaticMesh(
        UStaticMesh* StaticMesh,
        const FString& PackagePath,
        const FString& DMName,
        float Threshold,
        float FragilityRate,
        UPhysicalMaterial* PhysMat);
};

/**
 * AProceduralObjectInterpreterAPI
 * Primary Actor interface for triggering the import pipeline.
 */
UCLASS(Blueprintable)
class UPROCEDURALOBJECTINTERPRETER_API AProceduralObjectInterpreterAPI : public AActor
{
    GENERATED_BODY()

public:
    AProceduralObjectInterpreterAPI();

    UPROPERTY(EditAnywhere, Category = "Procedural|Config")
    FString SourceObjPath;

    UPROPERTY(EditAnywhere, Category = "Procedural|Config")
    FString SourceTexturePath;

    UPROPERTY(EditAnywhere, Category = "Procedural|Config")
    FString DestinationAssetPath = TEXT("/Game/ProceduralImports");

    UFUNCTION(CallInEditor, Category = "Procedural|Import")
    void TriggerImport()
    {
        ImportFromFiles(SourceObjPath, SourceTexturePath, DestinationAssetPath);
    }

    UFUNCTION(BlueprintCallable, Category = "Procedural|Import")
    FGeneratedAssets ImportFromFiles(const FString& ObjPath, const FString& TexturePath, const FString& DestinationPath);

protected:
    virtual void BeginPlay() override;

public:
    virtual void Tick(float DeltaTime) override;

private:
    /**
     * GenerateAndBuildStaticMesh
     * Fixed signature: UVs (FVector2D) then Normals (FVector) to match Franklin's .cpp implementation.
     */
    UStaticMesh* GenerateAndBuildStaticMesh(
        const FString& AssetName,
        const FString& PackagePath,
        const TArray<FVector>& Positions,
        const TArray<int32>& Indices,
        const TArray<FVector2D>& UVs,
        const TArray<FVector>& Normals,
        const TArray<int32>& FaceMaterialIndices,
        const TArray<FString>& MaterialSlotNames);

    UTexture2D* CreateTextureFromFile(const FString& FilePath, const FString& PackagePath, const FString& AssetName);

    AActor* SpawnStaticActor(UStaticMesh* MeshAsset, UPhysicalMaterial* PhysMat, FVector Location);

   AMyDestructibleActor* SpawnDestructibleActor(UDestructibleMesh* DMAsset, UPhysicalMaterial* PhysMat, FVector Location);

    void Internal_GenerateCollision(UStaticMesh* StaticMesh, const TArray<FVector>& Vertices);
};
//Last working version
