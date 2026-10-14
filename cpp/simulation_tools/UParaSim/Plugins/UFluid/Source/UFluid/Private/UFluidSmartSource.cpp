// Fill out your copyright notice in the Description page of Project Settings.


#include "UFluidSmartSource.h"
#include "Misc/Paths.h"


//constructor
AUFluidSmartSource::AUFluidSmartSource()
{

    // Control parameters
    Delta_Position=0.01; //cm

    Delta_Orientation= 0.5; //degree

    // Control commands
    Move_Up = false;

    Move_Down = false;

    Move_Front = false;

    Move_Back = false;

    Move_Left = false;

    Move_Right = false;

    Rotate_Right = false;

    Rotate_Left = false;

    Rotate_Up = false;

    Rotate_Down = false;

    Tilt_Right = false;

    Tilt_Left = false;

    PrimaryActorTick.bCanEverTick = true;

}

//destructor
AUFluidSmartSource::~AUFluidSmartSource()
{
    UE_LOG(LogTemp, Warning, TEXT("----------------------------------- KILLING SOURCE---------------------------------------"));
}


// Called when the game starts or when spawned
void AUFluidSmartSource::BeginPlay()
{
    Super::BeginPlay();
    UE_LOG(LogTemp, Warning,TEXT("Begin play!"));
}


// Called every frame
void AUFluidSmartSource::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    AUFluidSmartSource::Control();
}


// Control the cup
bool AUFluidSmartSource::Control(){

    //update object
    FVector translationB=this->GetActorLocation();
    FRotator rotationB=this->GetActorRotation();



   if( Move_Up ){
       translationB.Z+=Delta_Position;
        UE_LOG(LogTemp, Warning, TEXT("----------------------------------- Moving UP ---------------------------------------"));
   }

    if(Move_Down ){
        translationB.Z-=Delta_Position;
        UE_LOG(LogTemp, Warning, TEXT("----------------------------------- Moving DOWN ---------------------------------------"));
   }

    if(Move_Front){
        translationB.X+=Delta_Position;
        UE_LOG(LogTemp, Warning, TEXT("----------------------------------- Moving FRONT ---------------------------------------"));
   }

    if(Move_Back){
        translationB.X-=Delta_Position;
        UE_LOG(LogTemp, Warning, TEXT("----------------------------------- Moving BACK ---------------------------------------"));
   }

    if(Move_Left){
        translationB.Y-=Delta_Position;
        UE_LOG(LogTemp, Warning, TEXT("----------------------------------- Moving LEFT ---------------------------------------"));
   }

    if(Move_Right){
        translationB.Y+=Delta_Position;
        UE_LOG(LogTemp, Warning, TEXT("----------------------------------- Moving RIGHT ---------------------------------------"));
   }

    if(Rotate_Right){
        rotationB.Yaw+=Delta_Orientation;
        UE_LOG(LogTemp, Warning, TEXT("----------------------------------- Rotate RIGHT ---------------------------------------"));
   }

    if(Rotate_Left){
        rotationB.Yaw-=Delta_Orientation;
        UE_LOG(LogTemp, Warning, TEXT("----------------------------------- Rotate LEFT ---------------------------------------"));
   }
    if(Rotate_Up){
        rotationB.Pitch+=Delta_Orientation;
        UE_LOG(LogTemp, Warning, TEXT("----------------------------------- Rotate UP ---------------------------------------"));
   }

    if(Rotate_Down){
        rotationB.Pitch-=Delta_Orientation;
        UE_LOG(LogTemp, Warning, TEXT("----------------------------------- Rotate DOWN ---------------------------------------"));
   }

    if(Tilt_Right){
        rotationB.Roll+=Delta_Orientation;
        UE_LOG(LogTemp, Warning, TEXT("----------------------------------- Tilt RIGHT ---------------------------------------"));
   }

    if(Tilt_Left){
        rotationB.Roll-=Delta_Orientation;
        UE_LOG(LogTemp, Warning, TEXT("----------------------------------- Tilt LEFT ---------------------------------------"));
   }

    //update pose
    this->SetActorRotation(rotationB);
    this->SetActorLocation(translationB);

    return true;
}
