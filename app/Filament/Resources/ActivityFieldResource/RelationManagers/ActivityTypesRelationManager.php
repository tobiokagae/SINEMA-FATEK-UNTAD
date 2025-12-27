<?php

namespace App\Filament\Resources\ActivityFieldResource\RelationManagers;

use App\Models\ActivityType;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\RelationManagers\RelationManager;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\SoftDeletingScope;

class ActivityTypesRelationManager extends RelationManager
{
    protected static string $relationship = 'activityTypes';
    protected static ?string $title = 'Rubrik Kegiatan';

    public function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\TextInput::make('name')
                    ->label('Nama Kegiatan')
                    ->required()->maxLength(255),
                Forms\Components\TextInput::make('level')
                    ->label('Tingkat')
                    ->maxLength(255),
                Forms\Components\TextInput::make('achievement')
                    ->label('Peringkat')
                    ->maxLength(255),
                Forms\Components\TextInput::make('score')
                    ->label('Poin')
                    ->required()->numeric(),
                Forms\Components\Select::make('required_category')
                    ->label('Kategori Wajib')
                    ->options([
                        ActivityType::REQUIRED_CATEGORY_PKKMB => 'PKKMB (Wajib)',
                        ActivityType::REQUIRED_CATEGORY_BAKTI_LINGKUNGAN => 'Bakti Lingkungan (Wajib)',
                    ])
                    ->helperText('Pilih kategori ini hanya jika kegiatan tersebut adalah syarat wajib untuk permohonan transkrip.')
                    ->columnSpanFull(),
            ]);
    }

    public function table(Table $table): Table
    {
        return $table
            ->recordTitleAttribute('name')
            ->columns([
                Tables\Columns\TextColumn::make('name')->label('Nama Kegiatan')->searchable(),
                Tables\Columns\TextColumn::make('level')->label('Tingkat'),
                Tables\Columns\TextColumn::make('achievement')->label('Peringkat'),
                Tables\Columns\TextColumn::make('score')->label('Poin')->numeric(),
                Tables\Columns\TextColumn::make('required_category')
                    ->label('Kategori')
                    ->badge()
                    ->color(fn(?string $state): string => match ($state) {
                        ActivityType::REQUIRED_CATEGORY_PKKMB => 'success',
                        ActivityType::REQUIRED_CATEGORY_BAKTI_LINGKUNGAN => 'info',
                        default => 'gray',
                    })
                    ->formatStateUsing(fn(?string $state): string => match ($state) {
                        ActivityType::REQUIRED_CATEGORY_PKKMB => 'PKKMB',
                        ActivityType::REQUIRED_CATEGORY_BAKTI_LINGKUNGAN => 'Bakti Lingkungan',
                        default => '-',
                    })->searchable(),
            ])
            ->filters([
                //
            ])
            ->headerActions([
                Tables\Actions\CreateAction::make()
                    ->label('Rubrik Kegiatan')
                    ->icon('heroicon-s-plus')
                    ->modalHeading('Tambah Rubrik Kegiatan'),
            ])
            ->actions([
                Tables\Actions\ActionGroup::make([
                    Tables\Actions\EditAction::make(),
                    Tables\Actions\DeleteAction::make(),
                ]),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ]);
    }
}
