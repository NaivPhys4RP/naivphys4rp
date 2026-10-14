// Fill out your copyright notice in the Description page of Project Settings.


#include "UFluidEmitter.h"
#include <omp.h>


    // Sets default values

        UUFluidEmitter::UUFluidEmitter(){
            this->U_NumberParticles=300; //how many to emit in number of particles
            this->U_SampleVolume=0.1; //volume of sample in liter
            this->U_InVolume=false; //should it be emitted in volume
            this->U_EmissionRate=5; //how fast to emit
            this->U_WorldHandle=nullptr; //World handle
            this->U_IsPaused=false;
            this->U_FluidParticles={};
            this->U_ParticleModel=NewObject<UUFluidParticle>(); //particle model
            UE_LOG(LogTemp, Warning, TEXT("----------------------------------- CREATING EMITTER ---------------------------------------"));
            this->U_Color=false;
            //Unreal-Based Characterization
            this->U_ParticleModel->U_Type=P_STATIC_MESH;
            //this->U_ParticleModel->U_WorldHandle=nullptr;
            //this->U_ParticleModel->U_VolumeActor=nullptr;
            //this->U_ParticleModel->U_SkeletalMeshActor=nullptr;
            //this->U_ParticleModel->U_StaticMeshActor=nullptr;
            //this->U_ParticleModel->U_StaticMesh=nullptr;
            //this->U_ParticleModel->U_Mobility=EComponentMobility::Movable;
            FTransform tf(FRotator(0,0,0),FVector(0.0f,0.0f,0.0f),FVector(1.0f,1.0f,1.0f));
            this->U_ParticleModel->U_Transform=tf;
            //this->U_ParticleModel->U_SpawnParameters=new FActorSpawnParameters();
            this->U_ParticleModel->U_Material=nullptr;
            this->U_ParticleModel->U_Texture=nullptr;
            this->U_ParticleModel->U_PhysicalMaterial=nullptr;
            this->U_ParticleModel->U_PhysicsSimulation=false;
            this->U_ParticleModel->U_GravityEnabled=false;

            //Semantics-Based Characterization
            this->U_ParticleModel->IsBuilt=false;
            this->U_ParticleModel->IsSpawned=false;
            this->U_ParticleModel->Mass=0.13;              //kg
            this->U_ParticleModel->Density=0.0;
            this->U_ParticleModel->Destructibility=0.0;
            this->U_ParticleModel->Restitution=0.0;
            this->U_ParticleModel->Volume=0.0;		//m3
            this->U_ParticleModel->Friction=0.0;
            this->U_ParticleModel->Viscosity=0.0;
            this->U_ParticleModel->NS_Velocity=FVector(0.0f,0.0f,0.0f);	//Navier-Stockes Velocity
            this->U_ParticleModel->Linear_Damping=0.0;
            this->U_ParticleModel->Angular_Damping=0.0;
            this->U_ParticleModel->Color=FString(TEXT(""));
            this->U_ParticleModel->Material=FString(TEXT("Material'/UFluid/Particle/Materials/Green/M_Green.M_Green'"));
            this->U_ParticleModel->Physical_Material=FString(TEXT("PhysicalMaterial'/UFluid/Particle/PhysicalMaterials/Liquid/PM_FluidPhysicalMaterial.PM_FluidPhysicalMaterial'"));
            this->U_ParticleModel->Mesh=FString(TEXT("StaticMesh'/UFluid/Particle/Shapes/Sphere/SM_Sphere.SM_Sphere'"));
            this->U_ParticleModel->IsAlive=false;
            this->U_ParticleModel->Expected_Life_Time=0.0;  //in seconds
            this->U_ParticleModel->Remaning_Life_Time=0.0;  //in seconds
            this->U_ParticleModel->Particle_Index=FString(TEXT(""));
            this->U_ParticleModel->Particle_Reference=FString(TEXT(""));

            Fluid_Created=false;


        }

        UUFluidEmitter::UUFluidEmitter(UWorld* worldHandle, TArray<UUFluidParticle*> ListParticles)
    {
        this->U_NumberParticles=100; //how many to emit in number of particles
        this->U_SampleVolume=0.1; //volume of sample in liter
        this->U_InVolume=false; //should it be emitted in volume
                this->U_EmissionRate=5; //how fast to emit
                this->U_WorldHandle=worldHandle; //World handle
                this->U_IsPaused=false;
                this->U_FluidParticles=ListParticles;
                this->U_ParticleModel=NewObject<UUFluidParticle>(); //particle model
                UE_LOG(LogTemp, Warning, TEXT("----------------------------------- CREATING EMITTER ---------------------------------------"));

                //Unreal-Based Characterization
                this->U_ParticleModel->U_Type=P_STATIC_MESH;
                //this->U_ParticleModel->U_WorldHandle=nullptr;
                //this->U_ParticleModel->U_VolumeActor=nullptr;
                //this->U_ParticleModel->U_SkeletalMeshActor=nullptr;
                //this->U_ParticleModel->U_StaticMeshActor=nullptr;
                //this->U_ParticleModel->U_StaticMesh=nullptr;
                //this->U_ParticleModel->U_Mobility=EComponentMobility::Movable;
                FTransform tf(FRotator(0,0,0),FVector(0.0f,0.0f,0.0f),FVector(1.0f,1.0f,1.0f));
                this->U_ParticleModel->U_Transform=tf;
                //this->U_ParticleModel->U_SpawnParameters=new FActorSpawnParameters();
                this->U_ParticleModel->U_Material=nullptr;
                this->U_ParticleModel->U_Texture=nullptr;
                this->U_ParticleModel->U_PhysicalMaterial=nullptr;
                this->U_ParticleModel->U_PhysicsSimulation=false;
                this->U_ParticleModel->U_GravityEnabled=false;

                //Semantics-Based Characterization
                this->U_ParticleModel->IsBuilt=false;
                this->U_ParticleModel->IsSpawned=false;
                this->U_ParticleModel->Mass=0.13;              //kg
                this->U_ParticleModel->Density=0.0;
                this->U_ParticleModel->Restitution=0.0;
                this->U_ParticleModel->Volume=0.0;		//m3
                this->U_ParticleModel->Friction=0.0;
                this->U_ParticleModel->Viscosity=0.0;
                this->U_ParticleModel->Destructibility=0.0;
                this->U_ParticleModel->NS_Velocity=FVector(0.0f,0.0f,0.0f);	//Navier-Stockes Velocity
                this->U_ParticleModel->Linear_Damping=0.0;
                this->U_ParticleModel->Angular_Damping=0.0;
                this->U_ParticleModel->Color=FString(TEXT(""));
                this->U_ParticleModel->Material=FString(TEXT("/UFluid/Particle/Materials/Green/M_Green.M_Green"));
                this->U_ParticleModel->Mesh=FString(TEXT("/UFluid/Particle/PhysicalMaterials/Liquid/PM_FluidPhysicalMaterial.PM_FluidPhysicalMaterial"));
                this->U_ParticleModel->IsAlive=false;
                this->U_ParticleModel->Expected_Life_Time=0.0;  //in seconds
                this->U_ParticleModel->Remaning_Life_Time=0.0;  //in seconds
                this->U_ParticleModel->Particle_Index=FString(TEXT(""));
                this->U_ParticleModel->Particle_Reference=FString(TEXT(""));



    }

    //destructor
        UUFluidEmitter::~UUFluidEmitter()
    {
            UE_LOG(LogTemp, Warning, TEXT("----------------------------------- KILLING EMITTER ---------------------------------------"));
    }


    //method members
        bool UUFluidEmitter::StartEmission(FTransform SampleTransform){
            if(!this->U_WorldHandle){
                UE_LOG(LogTemp, Warning, TEXT("World handle for the emitter has not been properly set."));
                return false;
            }
            //update emitter transform through sample transform
              this->U_ParticleModel->U_Transform=SampleTransform;
              if (this->U_IsPaused)
                  return false;
              if (this->U_NumberParticles<1){
                  UUFluidEmitter::StopEmission();
                  Fluid_Created=true;
                  return false;
              }

              // Phase 1: Determine the exact number of particles to allocate and process for this run
              int32 ActualSpawnCount = 0;
              for(int i=0; i<this->U_EmissionRate; i++){
                  if(this->U_NumberParticles<1)
                      break;
                  this->U_NumberParticles--;
                  ActualSpawnCount++;
              }

              if (ActualSpawnCount <= 0) {
                  return true;
              }

              if(this->U_Color){
                  this->U_ParticleModel->Material=FString(TEXT("/UFluid/Particle/Materials/Red/M_Red.M_Red"));
              }

              // Phase 2: Main Thread Safe Allocation
              int32 StartingIndex = this->U_FluidParticles.Num();
              for(int32 i_omp = 0; i_omp < ActualSpawnCount; i_omp++) {
                  UUFluidParticle* TempParticle = NewObject<UUFluidParticle>();
                  this->U_FluidParticles.Add(TempParticle);
              }

              // Extract data pointers for raw OpenMP performance
              UUFluidParticle** RawParticlesPtr = this->U_FluidParticles.GetData();

              // Phase 3: Parallelized Heavy Initialization via OpenMP across 32 cores
              #pragma omp parallel for schedule(static)
              for(int32 i_omp = 0; i_omp < ActualSpawnCount; i_omp++){
                  UUFluidParticle* TaskParticle = RawParticlesPtr[StartingIndex + i_omp];

                  TaskParticle->U_StaticMesh=this->U_ParticleModel->U_StaticMesh;
                  TaskParticle->U_Material=this->U_ParticleModel->U_Material;
                  TaskParticle->U_PhysicalMaterial=this->U_ParticleModel->U_PhysicalMaterial;

                  TaskParticle->BuildParticle(this->U_WorldHandle,
                                              this->U_ParticleModel->U_Type,
                                              this->U_ParticleModel->U_Transform.GetLocation(),
                                              this->U_ParticleModel->U_Transform.GetRotation().Rotator(),
                                              this->U_ParticleModel->Scale,
                                              this->U_ParticleModel->Mesh,
                                              this->U_ParticleModel->Material,
                                              this->U_ParticleModel->Physical_Material,
                                              this->U_ParticleModel->Mass,
                                              this->U_ParticleModel->Linear_Damping,
                                              this->U_ParticleModel->Angular_Damping,
                                              this->U_ParticleModel->Restitution,
                                              this->U_ParticleModel->Friction,
                                              this->U_ParticleModel->Density);
              }

              // Phase 4: Sequential Main Thread Spawning Engine
              for(int32 i_omp = 0; i_omp < ActualSpawnCount; i_omp++){
                  RawParticlesPtr[StartingIndex + i_omp]->SpawnParticle();
              }

              return true;
    }

        bool UUFluidEmitter::PauseEmission(){
            this->U_IsPaused=true;
            return true;
    }

        bool UUFluidEmitter::StopEmission(){
              this->U_NumberParticles=0;
              UUFluidEmitter::PauseEmission();
              return true;
    }
