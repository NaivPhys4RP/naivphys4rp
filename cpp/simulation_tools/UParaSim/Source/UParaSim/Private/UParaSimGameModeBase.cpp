// Copyright Epic Games, Inc. All Rights Reserved.

#include "UParaSimGameModeBase.h"
#include "UParaSimMonitor.h"
#include "Engine/EngineBaseTypes.h"
#include "HighResScreenshot.h"
#include "IImageWrapper.h"
#include "RGBDCamera.h"
#include "RoboManager.h"
#include "ROS/Subscriber/ObjectStateSubscriber.h"
#include "ROS/Subscriber/BasePoseSubscriber.h"
#include "ROS/Subscriber/JointStatesSubscriber.h"
#include "IImageWrapperModule.h"
#include "UParaSimHUD.h"

//static variable definitions

int AUParaSimGameModeBase::NumberOfMaps=30;

TArray<FString> AUParaSimGameModeBase::MapList={};

FString AUParaSimGameModeBase::ActiveMap(TEXT(""));

FString AUParaSimGameModeBase::MainMap(TEXT(""));

UWorld* AUParaSimGameModeBase::ActiveWorldHandle=nullptr;

UWorld* AUParaSimGameModeBase::MainWorldHandle=nullptr;

TArray<UWorld*> AUParaSimGameModeBase::ListWorldHandles={};

FDelegateHandle AUParaSimGameModeBase::CleanupHandle=FDelegateHandle();

FDelegateHandle AUParaSimGameModeBase::TickHandle=FDelegateHandle();

TMap<UWorld*, FDelegateHandle> AUParaSimGameModeBase::CleanupHandles={};

TMap<UWorld*, FDelegateHandle> AUParaSimGameModeBase::TickHandles={};




AUParaSimGameModeBase::AUParaSimGameModeBase()
{
    /*// set default pawn class to our Blueprinted character
    static ConstructorHelpers::FClassFinder<APawn> PlayerPawnBPClass(TEXT("/Game/ThirdPersonCPP/Blueprints/ThirdPersonCharacter"));
    if (PlayerPawnBPClass.Class != NULL)
    {
        DefaultPawnClass = PlayerPawnBPClass.Class;
    }*/
    port=0;
    topic=0;
    DefaultPawnClass = ADefaultPawn::StaticClass();
    HUDClass=AUParaSimHUD::StaticClass();
    FApp::SetDeltaTime(0.002f);
    this->counter=0;
    //FApp::GetDeltaTime(1.0f);
    //create actor spawner
    this->ActorSpawner=new UParaSimActor();
    this->NumberOfParticles=AUParaSimGameModeBase::NumberOfMaps;
    this->MapPath="/home/franklin/Documents/Unreal Projects/UParaSim/Content/StarterContent/Maps/Minimal_Default";

    //enable thicking
    PrimaryActorTick.bCanEverTick = true;
}

void AUParaSimGameModeBase::BeginPlay()
{
  Super::BeginPlay();
  AUParaSimGameModeBase::NumberOfMaps=this->NumberOfParticles;
  GEngine->AddOnScreenDebugMessage(-1, 30, FColor::Red, TEXT("First Actor Spawning"));
  AUParaSimGameModeBase::MainWorldHandle=GetWorld();

}

void AUParaSimGameModeBase::Tick(float DeltaTime){
    Super::Tick(DeltaTime);
    GEngine->AddOnScreenDebugMessage(this->counter, 30, FColor::Green, TEXT("Game is thicking"));
    UE_LOG(LogTemp, Warning, TEXT("Debugging----- MAP NAME:  %s"), *GetWorld()->GetMapName());
    UE_LOG(LogTemp, Warning, TEXT("Debugging----- LOCAL URL:  %s"), *GetWorld()->GetLocalURL());
    UE_LOG(LogTemp, Warning, TEXT("Debugging----- ADDRESS URL:  %s"), *GetWorld()->PersistentLevel->URL.Map);
    UE_LOG(LogTemp, Warning, TEXT("Debugging----- ADDRESS URL:  %s"), *GetWorld()->GetFullName());
    UE_LOG(LogTemp, Warning, TEXT("Debugging----- NBR ACTORS:  %d"), GetWorld()->GetActorCount());
    UE_LOG(LogTemp, Warning, TEXT("Debugging----- WorldType:  %d"), GetWorld()->WorldType);
    this->counter++;
    if (this->counter==10){
        //creating different secondary worlds
        FString name(TEXT("Minimal_"));
        FString Filename(TEXT("/home/franklin/Desktop/UParaSim.jpg"));
        FString Path=this->MapPath;

        for(int i=0; i<AUParaSimGameModeBase::NumberOfMaps;i++){
            //AUParaSimGameModeBase::ListWorldHandles.Emplace(nullptr); Implicit in CreateWorld
            AUParaSimGameModeBase::CreateNewWorld(Path, AGameModeBase::StaticClass());
            //GetWorld()->GetGameViewport()->bDisableWorldRendering=true;
            if(AUParaSimGameModeBase::ListWorldHandles[i]->GetGameViewport()!=nullptr){
                //AUParaSimGameModeBase::ListWorldHandles[i]->GetGameViewport()->bDisableWorldRendering=true;
                AUParaSimGameModeBase::ListWorldHandles[i]->GetGameViewport()->bDisableWorldRendering=false;
                UE_LOG(LogTemp, Warning, TEXT("Debugging----- GAME VIEW PORT: IS WORKING "));
            }else
                UE_LOG(LogTemp, Warning, TEXT("Debugging----- GAME VIEW PORT: IS NOT WORKING "));
            this->ActorSpawner->BuildActor_V2(AUParaSimGameModeBase::ListWorldHandles[i]);
            //AUParaSimGameModeBase::ListWorldHandles[i]->Tick(ELevelTick::LEVELTICK_All, 1.0);
            TArray<FColor>ImageColor;
            this->ActorSpawner->VolumeActor->FollowCamera->CaptureScene();
            this->ActorSpawner->TVolumeActor[i]->FollowCamera->CaptureScene();
            AUParaSimGameModeBase::ReadColorImage(this->ActorSpawner->VolumeActor->FollowCamera->TextureTarget, ImageColor);
            //uint8* image=new uint8[ImageColor.Num()*3]; //three channels pro color
            //AUParaSimGameModeBase::ToColorImage(ImageColor, image);

            AUParaSimGameModeBase::SavePng(this->ActorSpawner->VolumeActor->FollowCamera->TextureTarget,ImageColor,Filename);
            UE_LOG(LogTemp, Warning, TEXT("Debugging----- IMAGE PIXEL CHANNEL:  IMAGE SAVED"));
            /*FIntPoint DestSize(w, h);

            FString ResultPath;
            FHighResScreenshotConfig& HighResScreenshotConfig = GetHighResScreenshotConfig();
            bool bSaved = HighResScreenshotConfig.SaveImage(Filename, OutBMP, DestSize, &ResultPath);


            UE_LOG(LogHTML5UI, Warning, TEXT("UHTML5UIWidget::SaveTexture2DDebug: %d %d"), w, h);
            UE_LOG(LogHTML5UI, Warning, TEXT("UHTML5UIWidget::SaveTexture2DDebug: %s %d"), *ResultPath, bSaved == true ? 1 : 0);*/


            UE_LOG(LogTemp, Warning, TEXT("Debugging----- MAP NAME:  %s"), *AUParaSimGameModeBase::ListWorldHandles[i]->GetMapName());
            UE_LOG(LogTemp, Warning, TEXT("Debugging----- LOCAL URL:  %s"), *AUParaSimGameModeBase::ListWorldHandles[i]->GetLocalURL());
            UE_LOG(LogTemp, Warning, TEXT("Debugging----- ADDRESS URL:  %s"), *AUParaSimGameModeBase::ListWorldHandles[i]->PersistentLevel->URL.Map);
            UE_LOG(LogTemp, Warning, TEXT("Debugging----- WORLD NAME:  %s"), *AUParaSimGameModeBase::ListWorldHandles[i]->GetFullName());
            UE_LOG(LogTemp, Warning, TEXT("Debugging----- NBR ACTORS:  %d"), AUParaSimGameModeBase::ListWorldHandles[i]->GetActorCount());
            UE_LOG(LogTemp, Warning, TEXT("Debugging----- WorldType:  %d"), AUParaSimGameModeBase::ListWorldHandles[i]->WorldType);
        }
    }else{
            if(this->counter==100){
                ;

                for(int i=0;i<AUParaSimGameModeBase::NumberOfMaps;i++){

                    int nb_obj=4;

                    for(int j=0;j<nb_obj;j++){
                        UStaticMeshComponent *StaticMeshComponent = Cast<AStaticMeshActor>(this->ActorSpawner->TStaticMeshActor[i*nb_obj+j])->GetStaticMeshComponent();
                        StaticMeshComponent->UnregisterComponent();

                        float delta_roll=FMath::RandRange(-2.0f,2.0f);
                        float delta_yaw=FMath::RandRange(-2.0f,2.0f);
                        float delta_pitch=FMath::RandRange(-2.0f,2.0f);

                        float delta_x=FMath::RandRange(-2.0f,2.0f);
                        float delta_y=FMath::RandRange(-2.0f,2.0f);
                        float delta_z=FMath::RandRange(-2.0f,2.0f);

                        //update object
                        FVector translationB=this->ActorSpawner->TStaticMeshActor[i*nb_obj+j]->GetActorLocation();
                        translationB.X+=delta_x;
                        translationB.Y+=delta_y;
                        translationB.Z+=delta_z;
                        this->ActorSpawner->TStaticMeshActor[i*nb_obj+j]->SetActorLocation(translationB);


                        FRotator rotationB=this->ActorSpawner->TStaticMeshActor[i*nb_obj+j]->GetActorRotation();
                        rotationB.Roll+=delta_roll;
                        rotationB.Yaw+=delta_yaw;
                        rotationB.Pitch+=delta_pitch;
                        this->ActorSpawner->TStaticMeshActor[i*nb_obj+j]->SetActorRotation(rotationB);

                        StaticMeshComponent->SetEnableGravity(true);
                        StaticMeshComponent->SetSimulatePhysics(true);
                        StaticMeshComponent->SetCollisionResponseToAllChannels(ECollisionResponse::ECR_Block);
                        StaticMeshComponent->SetGenerateOverlapEvents(true);
                        StaticMeshComponent->RegisterComponent();
                    }

                    float delta_roll=FMath::RandRange(-2.0f,2.0f);
                    float delta_yaw=FMath::RandRange(-2.0f,2.0f);
                    float delta_pitch=FMath::RandRange(-2.0f,2.0f);

                    float delta_x=FMath::RandRange(-2.0f,2.0f);
                    float delta_y=FMath::RandRange(-2.0f,2.0f);
                    float delta_z=FMath::RandRange(-2.0f,2.0f);

                    //transform Bowl
                    FVector translationB(243.0+delta_x,-276+delta_y,114+delta_z);
                    FRotator rotationB(0+delta_pitch, 0+delta_yaw, 0+delta_roll); //in degrees
                    //building material
                    FString mPathB = "Material'/Game/Bowl/M_Bowl.M_Bowl'";
                    //loading Mesh
                    FString stmPathB = "StaticMesh'/Game/Bowl/bowl.bowl'";
                    //spawn bowl
                    this->ActorSpawner->BuildActor_V3(AUParaSimGameModeBase::ListWorldHandles[i],translationB,rotationB,stmPathB,mPathB,0.80f);
                    UE_LOG(LogTemp, Warning, TEXT("Debugging----- CREATING BOWL IN WORLD/////////////////:  %d"), i);

                    delta_roll=FMath::RandRange(-2.0f,2.0f);
                    delta_yaw=FMath::RandRange(-2.0f,2.0f);
                    delta_pitch=FMath::RandRange(-2.0f,2.0f);

                    delta_x=FMath::RandRange(-2.0f,2.0f);
                    delta_y=FMath::RandRange(-2.0f,2.0f);
                    delta_z=FMath::RandRange(-2.0f,2.0f);

                    //transform Spoon
                    FVector translationS2(237+delta_x,delta_y-277,120+delta_z);
                    FRotator rotationS2(-30+delta_pitch,0+delta_yaw,0+delta_roll); //in degrees
                    //building material
                    FString mPathS2 = "Material'/Game/SoupSpoon/M_SoupSpoon.M_SoupSpoon'";
                    //loading Mesh
                    FString stmPathS2 = "StaticMesh'/Game/SoupSpoon/SM_SoupSpoon.SM_SoupSpoon'";
                    //spawn spoon
                    this->ActorSpawner->BuildActor_V3(AUParaSimGameModeBase::ListWorldHandles[i],translationS2,rotationS2,stmPathS2,mPathS2,0.3f);

                    delta_roll=FMath::RandRange(-4.0f,4.0f);
                    delta_yaw=FMath::RandRange(-4.0f,4.0f);
                    delta_pitch=FMath::RandRange(-2.0f,2.0f);

                    delta_x=FMath::RandRange(-2.0f,2.0f);
                    delta_y=FMath::RandRange(-2.0f,2.0f);
                    delta_z=FMath::RandRange(-2.0f,2.0f);

                    //transform Cup
                    FVector translationS1(255+delta_x,delta_y-262,114+delta_z);
                    FRotator rotationS1(0+delta_pitch,0+delta_yaw,0+delta_roll); //in degrees
                    //building material
                    FString mPathS1 = "Material'/Game/Models/M_Bowl.M_Bowl'";
                    //loading Mesh
                    FString stmPathS1 = "StaticMesh'/Game/Models/SM_Cup.SM_Cup'";
                    //spawn spoon
                    this->ActorSpawner->BuildActor_V3(AUParaSimGameModeBase::ListWorldHandles[i],translationS1,rotationS1,stmPathS1,mPathS1,0.5f);


                    delta_roll=FMath::RandRange(-2.0f,2.0f);
                    delta_yaw=FMath::RandRange(-2.0f,2.0f);
                    delta_pitch=FMath::RandRange(-2.0f,2.0f);

                    delta_x=FMath::RandRange(-5.0f,5.0f);
                    delta_y=FMath::RandRange(-5.0f,5.0f);
                    delta_z=FMath::RandRange(-2.0f,2.0f);

                    //transform Milk
                    FVector translationS3(249+delta_x,delta_y-237,114+delta_z);
                    FRotator rotationS3(0+delta_pitch,0+delta_yaw,0+delta_roll); //in degrees
                    //building material
                    FString mPathS3 = "Material'/Game/Models/M_Milk.M_Milk'";
                    //loading Mesh
                    FString stmPathS3 = "StaticMesh'/Game/Models/SM_Milk.SM_Milk'";
                    //spawn spoon
                    this->ActorSpawner->BuildActor_V3(AUParaSimGameModeBase::ListWorldHandles[i],translationS3,rotationS3,stmPathS3,mPathS3,1.0f);


                    delta_roll=FMath::RandRange(-2.0f,2.0f);
                    delta_yaw=FMath::RandRange(-2.0f,2.0f);
                    delta_pitch=FMath::RandRange(-2.0f,2.0f);

                    delta_x=FMath::RandRange(-5.0f,5.0f);
                    delta_y=FMath::RandRange(-5.0f,5.0f);
                    delta_z=FMath::RandRange(-2.0f,2.0f);

                    //transform Muesli
                    FVector translationS4(269+delta_x,delta_y-232,110+delta_z);
                    FRotator rotationS4(0+delta_pitch,60+delta_yaw,0+delta_roll); //in degrees
                    //building material
                    FString mPathS4 = "Material'/Game/Models/Muesli/M_KnusperSchoko1.M_KnusperSchoko1'";
                    //loading Mesh
                    FString stmPathS4 = "StaticMesh'/Game/Models/Muesli/SM_KnusperSchokoKeks1.SM_KnusperSchokoKeks1'";
                    //spawn spoon
                    this->ActorSpawner->BuildActor_V3(AUParaSimGameModeBase::ListWorldHandles[i],translationS4,rotationS4,stmPathS4,mPathS4,1.5f);


                    UE_LOG(LogTemp, Warning, TEXT("Debugging----- CREATING SPOON IN WORLD//////////////////:  %d"), i);
                }
            }
            if(this->counter>105){;

                for(int i=0;i<AUParaSimGameModeBase::NumberOfMaps;i++){
                    int nb_obj=4;

                    for(int j=0;j<nb_obj;j++){

                        float delta_roll=FMath::RandRange(-0.1f,0.1f);
                        float delta_yaw=FMath::RandRange(-0.1f,0.1f);
                        float delta_pitch=FMath::RandRange(-0.1f,0.1f);

                        float delta_x=FMath::RandRange(-0.1f,0.1f);
                        float delta_y=FMath::RandRange(-0.1f,0.1f);
                        float delta_z=FMath::RandRange(-0.1f,0.1f);

                        //update object
                        FVector translationB=this->ActorSpawner->TStaticMeshActor[i*nb_obj+j]->GetActorLocation();
                        translationB.X+=delta_x;
                        translationB.Y+=delta_y;
                        translationB.Z+=delta_z;
                        this->ActorSpawner->TStaticMeshActor[i*nb_obj+j]->SetActorLocation(translationB);


                        FRotator rotationB=this->ActorSpawner->TStaticMeshActor[i*nb_obj+j]->GetActorRotation();
                        rotationB.Roll+=delta_roll;
                        rotationB.Yaw+=delta_yaw;
                        rotationB.Pitch+=delta_pitch;
                        this->ActorSpawner->TStaticMeshActor[i*nb_obj+j]->SetActorRotation(rotationB);
                    }

                }
            }
            if (this->counter>10){
                for(int i=0; i<AUParaSimGameModeBase::NumberOfMaps;i++){
                this->ActorSpawner->TVolumeActor[i]->FollowCamera->CaptureScene();
                UE_LOG(LogTemp, Warning, TEXT("Debugging----- MAP NAME:  %s"), *AUParaSimGameModeBase::ListWorldHandles[i]->GetMapName());
                UE_LOG(LogTemp, Warning, TEXT("Debugging----- LOCAL URL:  %s"), *AUParaSimGameModeBase::ListWorldHandles[i]->GetLocalURL());
                UE_LOG(LogTemp, Warning, TEXT("Debugging----- ADDRESS URL:  %s"), *AUParaSimGameModeBase::ListWorldHandles[i]->PersistentLevel->URL.Map);
                UE_LOG(LogTemp, Warning, TEXT("Debugging----- WORLD NAME:  %s"), *AUParaSimGameModeBase::ListWorldHandles[i]->GetFullName());
                UE_LOG(LogTemp, Warning, TEXT("Debugging----- NBR ACTORS:  %d"), AUParaSimGameModeBase::ListWorldHandles[i]->GetActorCount());
                UE_LOG(LogTemp, Warning, TEXT("Debugging----- WorldType:  %d"), AUParaSimGameModeBase::ListWorldHandles[i]->WorldType);
                }
            }

    }
}





UWorld* AUParaSimGameModeBase::CreateNewWorld(FString map_name)
{

    UWorld* NewWorld = nullptr;
    UObject* WorldContextObject=GetWorld();

    //GEngine->AddOnScreenDebugMessage(-1, 15.0f, FColor::Yellow, FString::Printf(TEXT("level name = %s"), *LevelName2));

    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME:  %s"), *map_name);
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD PACKAGE NAME:  %s"), *FPackageName::FilenameToLongPackageName(map_name));

    UPackage* WorldPackage = FindPackage(nullptr, *FPackageName::FilenameToLongPackageName(map_name));
    if (WorldPackage == nullptr)
    {
        WorldPackage = LoadPackage(nullptr, *map_name, ELoadFlags::LOAD_None);
        if (!WorldPackage)
        {
            //GEngine->AddOnScreenDebugMessage(-1, 15.0f, FColor::Yellow, FString::Printf(TEXT("Package not loaded")));
            UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Package loading failed"));
            return nullptr;
        }

    }

    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Package successfully loaded"));
    UWorld* PackageWorld = UWorld::FindWorldInPackage(WorldPackage);

    UPackage* NewWorldPackage = CreatePackage(nullptr);

    FObjectDuplicationParameters Parameters(PackageWorld, NewWorldPackage);
    Parameters.DestName = PackageWorld->GetFName();
    Parameters.DestClass = PackageWorld->GetClass();
    Parameters.DuplicateMode = EDuplicateMode::PIE;
    Parameters.PortFlags = EPropertyPortFlags::PPF_Duplicate;

    NewWorld = CastChecked<UWorld>(StaticDuplicateObjectEx(Parameters));

    NewWorld->SetShouldTick(true);

    FWorldContext& WorldContext = GEngine->CreateNewWorldContext(EWorldType::Game);
    WorldContext.OwningGameInstance = UGameplayStatics::GetGameInstance(WorldContextObject);
    NewWorld->SetGameInstance(UGameplayStatics::GetGameInstance(WorldContextObject));
    NewWorld->WorldType = EWorldType::Game;
    WorldContext.SetCurrentWorld(NewWorld);

    //GEngine->AddOnScreenDebugMessage(-1, 15.0f, FColor::Yellow, FString::Printf(TEXT("CreateWorld: %s"), *NewWorld->GetFName().ToString()));

    //// In the PIE case the world will already have been initialized as part of CreatePIEWorldByDuplication
    if (!WorldContext.World()->bIsWorldInitialized)
    {
        WorldContext.World()->InitWorld();
    }


    FURL URL;
    //+ URL.AddOption(TEXT("GAME=/Game/Blueprints/GameModeBP_CreatedWorld.GameModeBP_CreatedWorld_C"));
    //+ WorldContext.World()->SetGameMode(URL);
    //WorldContext.World()->CreateAISystem();
    //+ WorldContext.World()->InitializeActorsForPlay(URL);

    for (auto actor : NewWorld->PersistentLevel->Actors) {
        UE_LOG(LogTemp, Warning, TEXT("LoadedWorldActorsClasses: %s"), *UKismetSystemLibrary::GetDisplayName(actor));
    }

    /*UFunction* Func = NewWorld->GetAuthGameMode()->GetClass()->FindFunctionByName(FName("Load"));
    if (Func == nullptr) {
        return nullptr;
    }
    FStructOnScope FuncParam(Func);
    NewWorld->GetAuthGameMode()->ProcessEvent(Func, FuncParam.GetStructMemory());*/
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Check GameMode successful"));
    WorldContext.World()->BeginPlay();
    WorldContext.World()->bWorldWasLoadedThisTick = true;
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Handle successful"));
    AUParaSimGameModeBase::ListWorldHandles.Add(NewWorld);
    return NewWorld;
}

UWorld* AUParaSimGameModeBase::CreateNewWorld(FString map_name, TSubclassOf<class AGameModeBase> GameMode)
{


    UWorld* NewWorld = nullptr;
    UObject* WorldContextObject=GetWorld();

    //*************************************************Creating game package****************************************************

    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME:  %s"), *map_name);
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD PACKAGE NAME:  %s"), *FPackageName::FilenameToLongPackageName(map_name));

    UPackage* WorldPackage = FindPackage(nullptr, *FPackageName::FilenameToLongPackageName(map_name));
    if (WorldPackage == nullptr)
    {
        WorldPackage = LoadPackage(nullptr, *map_name, ELoadFlags::LOAD_None);
        if (!WorldPackage)
        {
            //GEngine->AddOnScreenDebugMessage(-1, 15.0f, FColor::Yellow, FString::Printf(TEXT("Package not loaded")));
            UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Package loading failed"));
            return nullptr;
        }

    }

    if (!WorldPackage)
    {
        WorldPackage = CreatePackage(nullptr);
    }
    // Mark the package as containing a world.  This has to happen here rather than at serialization time,
    // so that e.g. the referenced assets browser will work correctly.
    if (WorldPackage != GetTransientPackage())
    {
        WorldPackage->ThisContainsMap();
    }

    //*************************************** Creating a new Package from the created one *****************************************

    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Creating new package ..."));

    UPackage* NewWorldPackage = CreatePackage(nullptr);
    NewWorldPackage->SetPackageFlags(PKG_PlayInEditor);
    NewWorldPackage->PIEInstanceID = WorldPackage->PIEInstanceID;
    NewWorldPackage->FileName = FName(*WorldPackage->GetName());
    NewWorldPackage->SetGuid(WorldPackage->GetGuid());
    NewWorldPackage->MarkAsFullyLoaded();

    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: New package created ..."));

    //********************************************** Creating New World from Package **************************************************
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Creating new world ..."));
    UWorld* PackageWorld = UWorld::FindWorldInPackage(WorldPackage);
    FObjectDuplicationParameters Parameters(PackageWorld, NewWorldPackage);
    Parameters.DestName = FName();
    Parameters.DestClass = PackageWorld->GetClass();
    Parameters.DuplicateMode = EDuplicateMode::PIE;
    Parameters.PortFlags = EPropertyPortFlags::PPF_Duplicate;
    NewWorld = CastChecked<UWorld>(StaticDuplicateObjectEx(Parameters));
    NewWorld->SetShouldTick(true);
    FWorldContext& WorldContext = GEngine->CreateNewWorldContext(EWorldType::Game);
    WorldContext.OwningGameInstance = UGameplayStatics::GetGameInstance(AUParaSimGameModeBase::GetMainWorldHandle());
    NewWorld->SetGameInstance(UGameplayStatics::GetGameInstance(AUParaSimGameModeBase::GetMainWorldHandle()));
    NewWorld->WorldType = EWorldType::PIE;
    WorldContext.SetCurrentWorld(NewWorld);
    NewWorld->AddToRoot();
    // Clear the dirty flags set during SpawnActor and UpdateLevelComponents
    WorldPackage->SetDirtyFlag(false);
    for (UPackage* ExternalPackage : WorldPackage->GetExternalPackages())
    {
        ExternalPackage->SetDirtyFlag(false);
    }

    // Tell the engine we are adding a world (unless we are asked not to)
    if (GEngine)
    {
        GEngine->WorldAdded(NewWorld);
    }

    auto GameInstance = UGameplayStatics::GetGameInstance(AUParaSimGameModeBase::GetMainWorldHandle());
    auto context = GameInstance->GetWorldContext()->GameViewport;
    WorldContext.GameViewport = context;
    //// In the PIE case the world will already have been initialized as part of CreatePIEWorldByDuplication
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: New world created ..."));
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Initializing new world ..."));
    if (!WorldContext.World()->bIsWorldInitialized)
    {
        WorldContext.World()->InitWorld();
    }
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: New world initialized ..."));

    //********************************************** Setting game mode for new world **************************************************

    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Setting Game Mode ..."));
    FURL URL;
    FString GamemodePath = FString("GAME=") + GameMode->GetPathName();
    UE_LOG(LogTemp, Warning, TEXT("GAME MODE OF NEW WORLD: %s"), *GamemodePath);
    const TCHAR* GMPath = *GamemodePath;
    URL.AddOption(GMPath);
    WorldContext.World()->SetGameMode(URL);
    WorldContext.World()->InitializeActorsForPlay(URL);
    for (auto actor : NewWorld->PersistentLevel->Actors) {
        UE_LOG(LogTemp, Warning, TEXT("LoadedWorldActorsClasses: %s"), *UKismetSystemLibrary::GetDisplayName(actor));
        if(UKismetSystemLibrary::GetDisplayName(actor).Find(FString("RGBDCamera"))>=0){
             ARGBDCamera* rgbdCam=Cast<ARGBDCamera>(actor);
             rgbdCam->ServerPort=10000+this->port;
             this->port++;
        }

        if(UKismetSystemLibrary::GetDisplayName(actor).Find(FString("RoboManager"))>=0){
             ARoboManager* robotManager=Cast<ARoboManager>(actor);
             Cast<UJointStatesSubscriber>(robotManager->ROSManager.ROSSubscribers[0])->CommonSubscriberParameters.Topic+=(FString("_")+FString::FromInt(this->topic));
             Cast<UBasePoseSubscriber>(robotManager->ROSManager.ROSSubscribers[1])->CommonSubscriberParameters.Topic+=(FString("_")+FString::FromInt(this->topic));
             Cast<UObjectStateSubscriber>(robotManager->ROSManager.ROSSubscribers[2])->CommonSubscriberParameters.Topic+=(FString("_")+FString::FromInt(this->topic));
             this->topic++;
        }

        if(UKismetSystemLibrary::GetDisplayName(actor).Find(FString("Canister"))>=0){
            this->ActorSpawner->TStaticMeshActor.Add(Cast<AStaticMeshActor>(actor));
        }
        if(UKismetSystemLibrary::GetDisplayName(actor).Find(FString("BottleMediumRinseFluidK"))>=0){
            this->ActorSpawner->TStaticMeshActor.Add(Cast<AStaticMeshActor>(actor));
        }
        if(UKismetSystemLibrary::GetDisplayName(actor).Find(FString("BottleSmallSoyBroth2"))>=0){
            this->ActorSpawner->TStaticMeshActor.Add(Cast<AStaticMeshActor>(actor));
        }

    }
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: RGBD Camera Created %d ..."), this->port);
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Robot Manager Created %d ..."), this->topic);
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Game mode is set ..."));

    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Begining Game ..."));
    WorldContext.World()->BeginPlay();
    WorldContext.World()->bWorldWasLoadedThisTick = true;
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Game Begun ..."));

    // Tick call in PIE
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Delegating ticking of worlds ..."));
    auto TickHandle2 = FWorldDelegates::OnWorldTickStart.AddLambda([NewWorld, this](UWorld* World, ELevelTick TickType, float DeltaSeconds) {
        if (World == AUParaSimGameModeBase::GetMainWorldHandle() && AUParaSimGameModeBase::GetMainWorldHandle()->WorldType == EWorldType::PIE) {
            auto TickHand = TickHandles.Find(NewWorld);
            if (TickHand->IsValid()) {
                if (NewWorld->ShouldTick())
                {
                    NewWorld->Tick(TickType, DeltaSeconds);
                    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: ************************************ TICKING STARTED ******************************************"));
                }

            }
        }});

        if (TickHandle2.IsValid())
        {
            GEngine->AddOnScreenDebugMessage(-1, 0.0f, FColor::Yellow, FString::Printf(TEXT("TickHackSet")));
            UE_LOG(LogTemp, Warning, TEXT("TickHackSet"));
        }
        TickHandles.Add(NewWorld, TickHandle2);
        UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Delegating for ticking created and saved  ..."));

        UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Delegating cleaning of worlds ..."));
        auto CHandle = FWorldDelegates::OnPostWorldCleanup.AddLambda([&,NewWorld](UWorld* World, bool bSessionEnded, bool bCleanupResources) {
            if (!AUParaSimGameModeBase::ListWorldHandles.Contains(World)) {;
                auto CLHandle = CleanupHandles.Find(NewWorld);
                UE_LOG(LogTemp, Warning, TEXT("DELEGATING CLEANING ------------------------------- 0 ---------------------------"));
                if (CLHandle) {
                    FWorldDelegates::OnPostWorldCleanup.Remove(*CLHandle);
                    CLHandle->Reset();
                    CleanupHandles.Remove(NewWorld);
                }
                UE_LOG(LogTemp, Warning, TEXT("DELEGATING CLEANING ------------------------------- 2 ---------------------------"));
                auto TickHand = TickHandles.Find(NewWorld);
                if (TickHand && TickHand->IsValid()) {
                    FWorldDelegates::OnWorldTickStart.Remove(*TickHand);
                    TickHand->Reset();
                    TickHandles.Remove(NewWorld);
                }

                UE_LOG(LogTemp, Warning, TEXT("DELEGATING CLEANING ------------------------------- 3 ---------------------------"));
                if (NewWorld) {
                    UE_LOG(LogTemp, Warning, TEXT("DELEGATING CLEANING ------------------------------- 3.1 ---------------------------"));

                    auto Name = NewWorld->GetMapName();
                    UE_LOG(LogTemp, Warning, TEXT("DELEGATING CLEANING ------------------------------- 3.2 ---------------------------"));

                    UE_LOG(LogTemp, Warning, TEXT("DELEGATING CLEANING ------------------------------- 3.3 ---------------------------"));

                    int l=0;
                    for (FActorIterator ActorIt(NewWorld); ActorIt; ++ActorIt)
                    {
                        UE_LOG(LogTemp, Warning, TEXT("DELEGATING CLEANING ------------------------------- 3.%d ---------------------------"),l++);
                        ActorIt->Destroy();

                    }
                    UE_LOG(LogTemp, Warning, TEXT("DELEGATING CLEANING ------------------------------- 1 ---------------------------"));
                    AUParaSimGameModeBase::ListWorldHandles.Remove(NewWorld);
                    UE_LOG(LogTemp, Warning, TEXT("DELEGATING CLEANING ------------------------------- 4 ---------------------------"));

                    GEngine->DestroyWorldContext(NewWorld);
                    NewWorld->DestroyWorld(true);
                    UE_LOG(LogTemp, Warning, TEXT("DELEGATING CLEANING ------------------------------- 5 ---------------------------"));
                    //GEngine->TrimMemory();
                    UE_LOG(LogTemp, Warning, TEXT("Created World destroyed: %s"), *Name);


                }
                UE_LOG(LogTemp, Warning, TEXT("DestroyedWorld: %s"), *World->GetFName().ToString());
            }
            });
    AUParaSimGameModeBase::CleanupHandles.Add(NewWorld, CHandle);
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Delegating for cleaning of worlds done and saved ..."));
    AUParaSimGameModeBase::ListWorldHandles.Add(NewWorld);
    UE_LOG(LogTemp, Warning, TEXT("CREATING WORLD NAME: Adding created world in the list of worlds ..."));
    //UWorldContext.SetWorldContext(&WorldContext);
    return NewWorld;
}













UWorld* AUParaSimGameModeBase::GetThisWorldHandle(){
    return nullptr;
}

UWorld* AUParaSimGameModeBase::GetActiveWorldHandle(){
    return ActiveWorldHandle;
}

UWorld* AUParaSimGameModeBase::GetMainWorldHandle(){
    MainWorldHandle=GEngine->GetCurrentPlayWorld();
    return MainWorldHandle;
}

bool AUParaSimGameModeBase::SwitchWorld(UWorld* TargetWorld){
    auto MainWorld = GetWorld();
    auto NewWorld = TargetWorld;
    if (!IsValid(NewWorld)){
        return false;
    }
    auto WorldContext = GEngine->GetWorldContextFromWorld(NewWorld);

    auto GameInstance = UGameplayStatics::GetGameInstance(MainWorld);
    if (!GameInstance) {
        UE_LOG(LogTemp, Warning, TEXT("AUParaSimGameModeBase::SwitchWorld - zero game instance in UWorld: %s"), *MainWorld->GetName());
        return false;
    }

    auto WContext = GameInstance->GetWorldContext();
    if (WContext) {
        auto viewport = WContext->GameViewport;
        if (IsValid(viewport)) {
            WorldContext->GameViewport = viewport;
        }
    }

    if (IsValid(NewWorld->GetGameViewport()) && IsValid(WorldContext->GameViewport) && NewWorld->GetGameViewport() != WorldContext->GameViewport) {
        NewWorld->GetGameViewport()->Init(*WorldContext, GameInstance);
    }

    /*auto vp = Cast<UUParaSimCommonGameViewportClient>(NewWorld->GetGameViewport());
    if (IsValid(vp)) {
        vp->ChangeRenderWorld(NewWorld);
    }*/
    return true;
}

bool AUParaSimGameModeBase::LoadWorld(FString TargetWorldMap){
    //this->ActiveWorldHandle=UWorld::CreateWorld();
    return true;
}

bool AUParaSimGameModeBase::LoadWorldAsync(FString TargetWorldMap){
    return true;
}

bool AUParaSimGameModeBase::SetShouldTickWhenInBackground(UWorld* TargetWorld, bool value){
    return true;
}

bool AUParaSimGameModeBase::EndWorld(UWorld* TargetWorld){
    return true;
}

bool AUParaSimGameModeBase::SpawnActor(UParaSimActor* TargetActor){
    return true;
}

bool AUParaSimGameModeBase::DeleteActor(UParaSimActor* TargetActor){
    return true;
}

void AUParaSimGameModeBase::ToColorImage( TArray<FColor> &ImageData, uint8 *Bytes){

        FColor *itI = ImageData.GetData();
        uint8_t *itO = Bytes;

        // Converts Float colors to bytes
        for(size_t i = 0; i < ImageData.Num(); ++i, ++itI, ++itO)
        {
            *itO = (uint8_t)itI->B;
            *++itO = (uint8_t)itI->G;
            *++itO = (uint8_t)itI->R;
        }
        return;
}

void AUParaSimGameModeBase::ReadColorImage(UTextureRenderTarget2D *RenderTarget, TArray<FColor> &ImageData){

        int32 RT_Width = RenderTarget->SizeX, RT_Height = RenderTarget->SizeY;
        FTextureRenderTargetResource* RenderTargetResource;
        ImageData.AddZeroed(RT_Width * RT_Height);
        RenderTargetResource = RenderTarget->GameThread_GetRenderTargetResource();
        FReadSurfaceDataFlags ReadSurfaceDataFlags;
        ReadSurfaceDataFlags.SetLinearToGamma(true); // This is super important to disable this!
        // Instead of using this flag, we will set the gamma to the correct value directly
        RenderTargetResource->ReadPixels(ImageData, ReadSurfaceDataFlags);

}


void AUParaSimGameModeBase::SavePng(UTextureRenderTarget2D* RenderTarget,TArray<FColor> Image, FString Filename)
{
    IImageWrapperModule& ImageWrapperModule = FModuleManager::LoadModuleChecked<IImageWrapperModule>(FName("ImageWrapper"));
    IImageWrapperPtr ImageWrapper = ImageWrapperModule.CreateImageWrapper(EImageFormat::JPEG);
    int32 Width = RenderTarget->SizeX, Height = RenderTarget->SizeY;
    ImageWrapper->SetRaw(Image.GetData(), Image.GetAllocatedSize(), Width, Height, ERGBFormat::BGRA, 8);
    const TArray<uint8, TSizedDefaultAllocator<64>>& ImgData = ImageWrapper->GetCompressed(100);
    FFileHelper::SaveArrayToFile(ImgData, *Filename);
}




