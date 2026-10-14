// Fill out your copyright notice in the Description page of Project Settings.


#include "UFluidParticle.h"
#include "Misc/Paths.h"

//constructor
UUFluidParticle::UUFluidParticle()
{
    //Unreal-Based Characterization
    this->U_State=S_CREATED;
    this->U_Type=P_STATIC_MESH;
    this->U_WorldHandle=nullptr;
    this->U_VolumeActor=nullptr;
    this->U_SkeletalMeshActor=nullptr;
    this->U_StaticMeshActor=nullptr;
    this->U_StaticMesh=nullptr;
    this->U_Mobility=EComponentMobility::Movable;
    FTransform tf(FRotator(0,0,0),FVector(0.0f,0.0f,0.0f),FVector(1.0f,1.0f,1.0f));
    this->U_Transform=tf;
    this->U_SpawnParameters=new FActorSpawnParameters();
    this->U_Material=nullptr;
    this->U_Texture=nullptr;
    this->U_PhysicalMaterial=nullptr;
    this->U_PhysicsSimulation=false;
    this->U_GravityEnabled=false;
    
    //Semantics-Based Characterization
    this->IsBuilt=false;
    this->IsSpawned=false;
    this->Mass=0.0;              //kg
    this->Density=0.0;
    this->Destructibility=0.0;
    this->Restitution=0.0;
    this->Volume=0.0;		//m3 
    this->Friction=0.0;
    this->Viscosity=0.0;
    this->NS_Velocity=FVector(0.0f,0.0f,0.0f);	//Navier-Stockes Velocity
    this->Linear_Damping=0.0;
    this->Angular_Damping=0.0;
    this->Color=FString(TEXT(""));
    this->Material=FString(TEXT(""));
    this->Physical_Material=FString(TEXT(""));
    this->Mesh=FString(TEXT(""));
    this->IsAlive=false;
    this->Expected_Life_Time=0.0;  //in seconds
    this->Remaning_Life_Time=0.0;  //in seconds
    this->Particle_Index=FString(TEXT(""));
    this->Particle_Reference=FString(TEXT(""));
}

//destructor
UUFluidParticle::~UUFluidParticle()
{
    UE_LOG(LogTemp, Warning, TEXT("----------------------------------- KILLING PARTICLE ---------------------------------------"));
}


//method members
bool UUFluidParticle::BuildParticle(UWorld* worldHandle,ParticleType type, FVector translation, FRotator rotation,
                                    FVector scale, FString mesh_path, FString material_path, FString physical_material_path,float mass, float linear_damping, float angular_damping, float restitution, float friction, float density){
    //setting parameters
    UE_LOG(LogTemp, Warning, TEXT("----------------------------------- Building Particle ---------------------------------------"));
    this->U_Type=type;  //type of particle
    this->U_WorldHandle=worldHandle;    //world handle in which to spawn
    this->U_StaticMeshActor=nullptr;    //actor is instantiated only during spawning
    if(!this->U_StaticMesh){
       this->U_StaticMesh = LoadStaticMeshFromPath(FName(*mesh_path)); //building static me
    }
    this->U_Mobility=EComponentMobility::Movable; //activate the actor's mobility
    FTransform tf(rotation, translation, scale);
    this->U_Transform=tf;   //transform
    if (this->U_SpawnParameters==nullptr)
         this->U_SpawnParameters=new FActorSpawnParameters();
    this->U_PhysicalMaterial=LoadPhysicalMaterialFromPath(*physical_material_path);
    if(!this->U_PhysicalMaterial){
        this->U_PhysicalMaterial = NewObject<UPhysicalMaterial>(UPhysicalMaterial::StaticClass(),TEXT("Fluid Physical Material"));
        this->Friction=friction;
        this->U_PhysicalMaterial->Friction=this->Friction;                                                    //friction

        this->Restitution=restitution;
        this->U_PhysicalMaterial->Restitution=this->Restitution;                                                 //restitution

        this->Density=density;
        this->U_PhysicalMaterial->Density=this->Density;                                                     //density

        this->U_PhysicalMaterial->bOverrideFrictionCombineMode=true;                                 //override friction combine mode
        this->U_PhysicalMaterial->FrictionCombineMode=EFrictionCombineMode::Multiply;                //friction combine mode


        this->U_PhysicalMaterial->bOverrideRestitutionCombineMode=true;                              //override restitution combine mode
        this->U_PhysicalMaterial->RestitutionCombineMode=EFrictionCombineMode::Multiply;          //restitution combine mode

        this->U_PhysicalMaterial->StaticFriction=this->Friction;                                              //static friction
    }
    if(!this->U_Material){
       this->U_Material=LoadMaterialFromPath(*material_path);
    }
    this->U_Texture=nullptr;
    this->U_PhysicsSimulation=true; //enabling physics
    this->U_GravityEnabled=true;
    this->IsBuilt=true;
    this->Mass=mass;
    this->Linear_Damping=linear_damping;
    this->Angular_Damping=angular_damping;
    this->U_State=S_BUILT;
    return true;
}

bool UUFluidParticle::SpawnParticle(){
    if (!this->IsBuilt)
        return false;
    UE_LOG(LogTemp, Warning, TEXT("----------------------------------- Spawning Particle ---------------------------------------"));
    this->U_StaticMeshActor=this->U_WorldHandle->SpawnActor<AStaticMeshActor>( AStaticMeshActor::StaticClass(), this->U_Transform, *(this->U_SpawnParameters));
    UStaticMeshComponent *StaticMeshComponent = Cast<AStaticMeshActor>(this->U_StaticMeshActor)->GetStaticMeshComponent();
    StaticMeshComponent->UnregisterComponent();

    /************************ Visual Model of Particles / appearance  *******************************/
    StaticMeshComponent->SetStaticMesh(this->U_StaticMesh); //shape
    StaticMeshComponent->SetMaterial(0,this->U_Material);  //material+texture


    /************************ Physical Model of Particles / behaviour  *******************************/
    //this->U_PhysicalMaterial->

    StaticMeshComponent->SetSimulatePhysics(this->U_PhysicsSimulation);                         //enable Physics
    StaticMeshComponent->SetMobility(this->U_Mobility);                                         //mobility
    StaticMeshComponent->SetMassOverrideInKg(NAME_None, this->Mass,false);                       //mass
    StaticMeshComponent->SetLinearDamping(this->Linear_Damping);                                //linear damping
    StaticMeshComponent->SetAngularDamping(this->Angular_Damping);                              //angular damping
    StaticMeshComponent->SetEnableGravity(this->U_GravityEnabled);                              //enable Gravity


    //StaticMeshComponent->AddForce(FVector(0.0f,0.0f,0.0f));                                     //adding force
    //StaticMeshComponent->GetBodyInstance()->SetLinearVelocity(FVector(0.0f,0.0f,0.0f), false);       //adding velocity

    StaticMeshComponent->SetPhysMaterialOverride(this->U_PhysicalMaterial);                     //container for above properties

    StaticMeshComponent->SetCollisionResponseToAllChannels(ECollisionResponse::ECR_Block);       //enable collision
    StaticMeshComponent->SetGenerateOverlapEvents(true);
    StaticMeshComponent->RegisterComponent();

    /************************ World-Space Bounds & Volume Check *******************************/
    FBoxSphereBounds WorldBounds = StaticMeshComponent->Bounds;
    FVector WorldDimensions = WorldBounds.BoxExtent * 2.0f;
    float WorldRadius = WorldBounds.BoxExtent.X; // Half-extent is the radius for a uniform sphere
    CachedParticleSide=WorldRadius*2;
    float SingleParticleVolume = (4.0f / 3.0f) * PI * (WorldRadius * WorldRadius * WorldRadius);

    UE_LOG(LogTemp, Log, TEXT("World-Space Dimensions (X x Y x Z): %s"), *WorldDimensions.ToString());
    UE_LOG(LogTemp, Log, TEXT("World-Space Radius: %f cm"), WorldRadius);
    UE_LOG(LogTemp, Log, TEXT("World-Space Side: %f cm"), CachedParticleSide);
    UE_LOG(LogTemp, Log, TEXT("Calculated Single Particle Volume: %f cm³"), SingleParticleVolume);
    /******************************************************************************************/

    this->IsSpawned=true;
    //making particle visible
    this->U_StaticMeshActor->SetActorHiddenInGame(false);
    this->U_StaticMeshActor->SetHidden(false);
    this->U_State=S_SPAWNED;
    return true;
}

bool UUFluidParticle::UpdateParticle(){
      return false;
}


//deleting an actor
bool UUFluidParticle::DeleteParticle(){
    //delete object
    if(!this->IsSpawned)
        return false;
    if(this->U_StaticMeshActor!=nullptr)
        this->U_WorldHandle->DestroyActor(this->U_StaticMeshActor);
    return true;
}


bool UUFluidParticle::WeakenParticle(float Impact){
      return false;
}

bool UUFluidParticle::WeakenParticle(){
      return false;
}


//utility method
template <typename ObjClass>
ObjClass* UUFluidParticle::LoadObjFromPath(const FName& Path)
{
if (Path == NAME_None) return nullptr;

return Cast<ObjClass>(StaticLoadObject(ObjClass::StaticClass(), nullptr, *Path.ToString()));
}

UMaterial* UUFluidParticle::LoadMaterialFromPath(const FName& Path)
{
if (Path == NAME_None) return nullptr;
return LoadObjFromPath<UMaterial>(Path);
}

UPhysicalMaterial* UUFluidParticle::LoadPhysicalMaterialFromPath(const FName& Path)
{
if (Path == NAME_None) return nullptr;
return LoadObjFromPath<UPhysicalMaterial>(Path);
}

UStaticMesh* UUFluidParticle::LoadStaticMeshFromPath(const FName& Path)
{
if (Path == NAME_None) return nullptr;
return LoadObjFromPath<UStaticMesh>(Path);
}


