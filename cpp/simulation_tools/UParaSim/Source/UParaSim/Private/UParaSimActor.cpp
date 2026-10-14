// Fill out your copyright notice in the Description page of Project Settings.


#include "UParaSimActor.h"
#include "Misc/Paths.h"

//constructor
UParaSimActor::UParaSimActor()
{
    this->Type=STATIC_MESH;
    this->VolumeActor=nullptr;
    this->TVolumeActor={};
    this->SkeletalMeshActor=nullptr;
    this->StaticMeshActor=nullptr;
    this->TStaticMeshActor={};
    this->StaticMesh=nullptr;
    this->PhysicsSimulation=true;
    this->Material=nullptr;
    this->Mobility=EComponentMobility::Movable;
    FTransform tf(FRotator(0,0,0),FVector(0.0f,0.0f,0.0f),FVector(1.0f,1.0f,1.0f));
    this->Transform=tf;
    this->SpawnParameters=new FActorSpawnParameters();
}

//destructor
UParaSimActor::~UParaSimActor()
{
}


template <typename ObjClass>
ObjClass* UParaSimActor::LoadObjFromPath(const FName& Path)
{
if (Path == NAME_None) return nullptr;

return Cast<ObjClass>(StaticLoadObject(ObjClass::StaticClass(), nullptr, *Path.ToString()));
}

UMaterial* UParaSimActor::LoadMaterialFromPath(const FName& Path)
{
if (Path == NAME_None) return nullptr;
return LoadObjFromPath<UMaterial>(Path);
}

UStaticMesh* UParaSimActor::LoadStaticMeshFromPath(const FName& Path)
{
if (Path == NAME_None) return nullptr;
return LoadObjFromPath<UStaticMesh>(Path);
}

//deleting an actor
bool UParaSimActor::DeleteActor(UWorld* worldHandle){
    //delete object
    if(this->StaticMeshActor!=nullptr)
        worldHandle->DestroyActor(this->StaticMeshActor);
    return true;
}

//building an actor
bool UParaSimActor::BuildActor(UWorld* worldHandle){

    FString RelativePath = FPaths::ProjectContentDir();
    FString FullPath = IFileManager::Get().ConvertToAbsolutePathForExternalAppForRead(*RelativePath);
    FName class_descriptor;
    FName material_descriptor;
    EComponentMobility::Type mobility;
    bool physicsSimulation=true;

    //Building the transform

    FVector translation(0, 0, 0);
    FRotator rotation(0, 0, 0); //in degrees
    FVector scale(1, 1, 1);

    FTransform objectTransform(rotation, translation, scale);
    this->Transform=objectTransform;
    //building material

    FString mPath = "Material'/Game/Bowl/M_Bowl.M_Bowl'";
    material_descriptor=FName(*mPath);
    this->Material = LoadMaterialFromPath(material_descriptor);

    //loading Mesh
    FString stmPath = "StaticMesh'/Game/Bowl/bowl.bowl'";
    class_descriptor=FName(*stmPath);
    this->StaticMesh = LoadStaticMeshFromPath(class_descriptor);

    //setting mobility
    this->Mobility=EComponentMobility::Movable;

    //enabling physics
    this->PhysicsSimulation=true;


    this->StaticMeshActor=worldHandle->SpawnActor<AStaticMeshActor>( AStaticMeshActor::StaticClass(), this->Transform, *(this->SpawnParameters) );
    UStaticMeshComponent *StaticMeshComponent = Cast<AStaticMeshActor>(this->StaticMeshActor)->GetStaticMeshComponent();
    StaticMeshComponent->UnregisterComponent();
    StaticMeshComponent->SetStaticMesh(this->StaticMesh);
    StaticMeshComponent->SetMaterial(0,this->Material);
    StaticMeshComponent->SetMobility(this->Mobility);
    StaticMeshComponent->SetMassOverrideInKg(NAME_None, 1.0,true);
    StaticMeshComponent->SetSimulatePhysics(this->PhysicsSimulation);
    StaticMeshComponent->SetEnableGravity(this->PhysicsSimulation);
    StaticMeshComponent->SetCollisionResponseToAllChannels(ECollisionResponse::ECR_Block);
    StaticMeshComponent->SetGenerateOverlapEvents(true);
    StaticMeshComponent->RegisterComponent();
    return true;
}


//building an actor
bool UParaSimActor::BuildActor_V3(UWorld* worldHandle, FVector translation, FRotator rotation, FString mesh_path, FString material_path,float mass){

    FString RelativePath = FPaths::ProjectContentDir();
    FString FullPath = IFileManager::Get().ConvertToAbsolutePathForExternalAppForRead(*RelativePath);
    FName class_descriptor;
    FName material_descriptor;
    EComponentMobility::Type mobility;
    bool physicsSimulation=true;

    //Building the transform
     FVector scale(1, 1, 1);
    FTransform objectTransform(rotation, translation, scale);
    this->Transform=objectTransform;
    //building material

    UE_LOG(LogTemp, Warning, TEXT("Debugging----- CREATING MESH IN WORLD/////////////////:  %s"), *mesh_path);
    UE_LOG(LogTemp, Warning, TEXT("Debugging----- CREATING MATERIAL IN WORLD/////////////////:  %s"), *material_path);
    material_descriptor=FName(*material_path);
    this->Material = LoadMaterialFromPath(material_descriptor);

    //loading Mesh
    class_descriptor=FName(*mesh_path);
    this->StaticMesh = LoadStaticMeshFromPath(class_descriptor);

    //setting mobility
    this->Mobility=EComponentMobility::Movable;

    //enabling physics
    this->PhysicsSimulation=true;


    this->StaticMeshActor=worldHandle->SpawnActor<AStaticMeshActor>( AStaticMeshActor::StaticClass(), this->Transform, *(this->SpawnParameters));
    UStaticMeshComponent *StaticMeshComponent = Cast<AStaticMeshActor>(this->StaticMeshActor)->GetStaticMeshComponent();
    StaticMeshComponent->UnregisterComponent();
    StaticMeshComponent->SetStaticMesh(this->StaticMesh);
    StaticMeshComponent->SetMaterial(0,this->Material);
    StaticMeshComponent->SetMobility(this->Mobility);
    StaticMeshComponent->SetMassOverrideInKg(NAME_None, mass,true);
    StaticMeshComponent->SetSimulatePhysics(this->PhysicsSimulation);
    StaticMeshComponent->SetEnableGravity(this->PhysicsSimulation);
    StaticMeshComponent->SetCollisionResponseToAllChannels(ECollisionResponse::ECR_Block);
    StaticMeshComponent->SetGenerateOverlapEvents(true);
    StaticMeshComponent->RegisterComponent();
    this->TStaticMeshActor.Add(this->StaticMeshActor);
    return true;
}


//building an actor
bool UParaSimActor::BuildActor(FName class_descriptor, FName material_descriptor, FRotator rotation,
                FVector translation, FVector scale, EComponentMobility::Type mobility, bool physicsSimulation){

    FString RelativePath = FPaths::ProjectContentDir();
    FString FullPath = IFileManager::Get().ConvertToAbsolutePathForExternalAppForRead(*RelativePath);

    return true;
}


//building an actor version 2
bool UParaSimActor::BuildActor_V2(UWorld* worldHandle){

    FString RelativePath = FPaths::ProjectContentDir();
    FString FullPath = IFileManager::Get().ConvertToAbsolutePathForExternalAppForRead(*RelativePath);
    FName class_descriptor;
    FName material_descriptor;
    EComponentMobility::Type mobility;
    bool physicsSimulation=true;

    //Building the transform

    FVector translation(-90+420+4130, 20-270,150);
    FRotator rotation(-30, 180, 0); //in degrees
    FVector scale(1, 1, 1);

    FTransform objectTransform(rotation, translation, scale);
    this->Transform=objectTransform;

    //setting mobility
    this->Mobility=EComponentMobility::Movable;

    //enabling physics
    //this->PhysicsSimulation=true;


    this->VolumeActor=worldHandle->SpawnActor<AUParaSimMonitor>( AUParaSimMonitor::StaticClass(), this->Transform, *(this->SpawnParameters));
    //this->VolumeActor->SetMobility(this->Mobility);

    this->TVolumeActor.Add(this->VolumeActor);

    return true;
}



