<?php

namespace App\Filament\Resources;

use App\Filament\Resources\SignatoryResource\Pages;
use App\Models\Signatory;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Support\Facades\Auth;

class SignatoryResource extends Resource
{
    protected static ?string $model = Signatory::class;
    protected static ?string $navigationIcon = 'heroicon-o-pencil-square';
    protected static ?string $navigationGroup = 'Pengaturan';
    protected static ?string $navigationLabel = 'Penandatangan';
    protected static ?string $modelLabel = 'Penandatangan';
    protected static ?string $pluralLabel = 'Penandatangan';

    public static function canViewAny(): bool
    {
        return Auth::user()->role === 'Admin';
    }

    public static function canCreate(): bool
    {
        return false;
    }

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Select::make('faculty_id')
                    ->relationship('faculty', 'name')
                    ->label('Fakultas')
                    ->required()
                    ->unique(ignoreRecord: true),
                Forms\Components\TextInput::make('name')
                    ->label('Nama Lengkap (dengan gelar)')
                    ->required(),
                Forms\Components\TextInput::make('nip')
                    ->label('NIP')
                    ->required(),
                Forms\Components\TextInput::make('jabatan')
                    ->default('Wakil Dekan Bidang Kemahasiswaan dan Alumni')
                    ->required(),
                Forms\Components\TextInput::make('pangkat')
                    ->placeholder('Pembina Tingkat I')
                    ->label('Pangkat')
                    ->required(),
                Forms\Components\TextInput::make('golongan')
                    ->placeholder('IV/b')
                    ->label('Golongan')
                    ->required(),

                Forms\Components\FileUpload::make('signature_image_path')
                    ->label('Gambar Tanda Tangan')
                    ->disk('public')
                    ->directory('signatures')
                    ->image()
                    ->helperText('Unggah gambar dengan latar belakang transparan (PNG).'),

                Forms\Components\FileUpload::make('stamp_image_path')
                    ->label('Gambar Cap Fakultas')
                    ->disk('public')
                    ->directory('stamps')
                    ->image()
                    ->helperText('Unggah gambar dengan latar belakang transparan (PNG).'),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('faculty.name')->label('Fakultas')->sortable(),
                Tables\Columns\TextColumn::make('name')->label('Nama Pejabat')->searchable(),
                Tables\Columns\TextColumn::make('nip')->label('NIP'),
                Tables\Columns\TextColumn::make('jabatan')->label('Jabatan'),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
            ]);
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListSignatories::route('/'),
            // 'create' => Pages\CreateSignatory::route('/create'),
            // 'edit' => Pages\EditSignatory::route('/{record}/edit'),
        ];
    }
}
