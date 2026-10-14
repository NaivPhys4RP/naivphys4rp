// Fill out your copyright notice in the Description page of Project Settings.


#include "UParaSimMonitor.h"


// Sets default values
AUParaSimMonitor::AUParaSimMonitor()
{

    // Create a camera boom (pulls in towards the player if there is a collision)
    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(RootComponent);
    CameraBoom->TargetArmLength = 1.0f; // The camera follows at this distance behind the character
    CameraBoom->bUsePawnControlRotation = true; // Rotate the arm based on the controller
    this->timer=0;
    this->direction=1;

    // Create a follow camera
    FollowCamera = CreateDefaultSubobject<UUParaSimSceneCaptureComponent2D>(TEXT("FollowCamera"));
    FollowCamera->TextureTarget = NewObject<UTextureRenderTarget2D>();
    FollowCamera->TextureTarget->InitAutoFormat(640, 480);
    FollowCamera->TextureTarget->UpdateResourceImmediate();
    FollowCamera->CaptureSource=SCS_SceneColorHDR;
    FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName); // Attach the camera to the end of the boom and let the boom adjust to match the controller orientation
    FollowCamera->bCaptureEveryFrame=true;
    // Set this pawn to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
    PrimaryActorTick.bCanEverTick = true;

}

// Called when the game starts or when spawned
void AUParaSimMonitor::BeginPlay()
{
    Super::BeginPlay();

}

// Called every frame
void AUParaSimMonitor::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);
    FRotator r=this->GetActorRotation();
    /*//int delta_roll=FMath::RandRange(0,0);
    int delta_yaw=FMath::RandRange(1,10);
    //int delta_pitch=FMath::RandRange(0,0);*/

    if(this->timer<=15 && this->timer>=-15){
        r.Add(0.0,1.0*this->direction,0.0);
        this->timer+=this->direction;
     }else{
        if(this->timer>15){
            this->direction=-1;
            this->timer+=this->direction;
            r.Add(0.0,1.0*this->direction,0.0);
        }else{
            this->direction=1;
            this->timer+=this->direction;
            r.Add(0.0,1.0*this->direction,0.0);
        }
    }
    this->SetActorRotation(r);
}

// Called to bind functionality to input
void AUParaSimMonitor::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

    /*

// Set up gameplay key bindings
    check(PlayerInputComponent);
    PlayerInputComponent->BindAction("Jump", IE_Pressed, this, &ACharacter::Jump);
    PlayerInputComponent->BindAction("Jump", IE_Released, this, &ACharacter::StopJumping);

    PlayerInputComponent->BindAxis("MoveForward", this, &AAIHNSAMAPCharacter::MoveForward);
    PlayerInputComponent->BindAxis("MoveRight", this, &AAIHNSAMAPCharacter::MoveRight);

    // We have 2 versions of the rotation bindings to handle different kinds of devices differently
    // "turn" handles devices that provide an absolute delta, such as a mouse.
    // "turnrate" is for devices that we choose to treat as a rate of change, such as an analog joystick
    PlayerInputComponent->BindAxis("Turn", this, &APawn::AddControllerYawInput);
    PlayerInputComponent->BindAxis("TurnRate", this, &AAIHNSAMAPCharacter::TurnAtRate);
    PlayerInputComponent->BindAxis("LookUp", this, &APawn::AddControllerPitchInput);
    PlayerInputComponent->BindAxis("LookUpRate", this, &AAIHNSAMAPCharacter::LookUpAtRate);

    // handle touch devices
    PlayerInputComponent->BindTouch(IE_Pressed, this, &AAIHNSAMAPCharacter::TouchStarted);
    PlayerInputComponent->BindTouch(IE_Released, this, &AAIHNSAMAPCharacter::TouchStopped);

    // VR headset functionality
    PlayerInputComponent->BindAction("ResetVR", IE_Pressed, this, &AAIHNSAMAPCharacter::OnResetVR);


*/

}

