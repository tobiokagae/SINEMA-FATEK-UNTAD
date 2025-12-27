<?php

namespace App\Filament\Pages;

use App\Models\Setting;
use Filament\Actions\Action;
use Filament\Forms\Components\FileUpload;
use Filament\Forms\Components\Grid;
use Filament\Forms\Components\Section;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Tabs; // <-- 1. Import komponen Tabs
use Filament\Forms\Components\TextInput;
use Filament\Forms\Concerns\InteractsWithForms;
use Filament\Forms\Contracts\HasForms;
use Filament\Forms\Form;
use Filament\Forms\Get;
use Filament\Notifications\Notification;
use Filament\Pages\Page;
use Illuminate\Support\Carbon;
use Illuminate\Support\Facades\Auth;

class Settings extends Page implements HasForms
{
    use InteractsWithForms;

    protected static ?string $navigationIcon = 'heroicon-o-cog-6-tooth';
    protected static ?string $navigationGroup = 'Pengaturan';
    protected static ?string $navigationLabel = 'Umum';
    protected static ?string $title = 'Umum';
    protected static string $view = 'filament.pages.settings';

    public ?array $data = [];

    public function mount(): void
    {
        // Ambil semua pengaturan yang relevan dari database
        $settings = Setting::whereIn('key', [
            'kop_surat_logo',
            'claim_restriction_mode',
            'claim_max_days',
            'semester_ganjil_start_month',
            'semester_ganjil_end_month',
            'semester_genap_start_month',
            'semester_genap_end_month',
        ])->pluck('value', 'key')->toArray();

        $this->form->fill($settings);
    }

    public function form(Form $form): Form
    {
        $months = collect(range(1, 12))->mapWithKeys(fn($month) => [$month => Carbon::create()->month($month)->translatedFormat('F')]);

        return $form
            ->schema([
                // --- 2. Bungkus semua field dengan komponen Tabs ---
                Tabs::make('Tabs')
                    ->tabs([
                        // --- TAB 1: PENGATURAN KOP SURAT ---
                        Tabs\Tab::make('Kop Surat')
                            ->icon('heroicon-o-document-text')
                            ->schema([
                                FileUpload::make('kop_surat_logo')
                                    ->label('Logo Kop Surat')
                                    ->disk('public')
                                    ->directory('logos')
                                    ->image()
                                    ->helperText('Unggah logo baru untuk menggantikan yang lama di transkrip.'),
                            ]),

                        // --- TAB 2: PENGATURAN PEMBATASAN KLAIM ---
                        Tabs\Tab::make('Pembatasan Klaim')
                            ->icon('heroicon-o-calendar-days')
                            ->schema([
                                Section::make('Mode Pembatasan Klaim')
                                    ->description('Pilih aturan yang akan diterapkan saat mahasiswa mengajukan klaim kegiatan.')
                                    ->schema([
                                        Select::make('claim_restriction_mode')
                                            ->label('Mode Pembatasan')
                                            ->options([
                                                'none' => 'Tidak Ada Batasan',
                                                'days' => 'Berdasarkan Jumlah Hari',
                                                'semester' => 'Berdasarkan Periode Semester',
                                            ])
                                            ->default('none')
                                            ->live()
                                            ->required(),
                                    ]),
                                Section::make('Pengaturan Batas Hari')
                                    ->visible(fn(Get $get) => $get('claim_restriction_mode') === 'days')
                                    ->schema([
                                        TextInput::make('claim_max_days')
                                            ->label('Batas Maksimal Hari (setelah tanggal sertifikat)')
                                            ->numeric()
                                            ->required()
                                            ->minValue(1)
                                            ->suffix('hari')
                                            ->helperText('Contoh: Jika diisi 30, sertifikat yang terbit lebih dari 30 hari yang lalu tidak bisa diklaim.'),
                                    ]),
                                Section::make('Pengaturan Periode Semester')
                                    ->visible(fn(Get $get) => $get('claim_restriction_mode') === 'semester')
                                    ->schema([
                                        Grid::make(2)->schema([
                                            Select::make('semester_ganjil_start_month')->label('Semester Ganjil Dimulai')->options($months)->required(),
                                            Select::make('semester_ganjil_end_month')->label('Semester Ganjil Berakhir')->options($months)->required(),
                                        ]),
                                        Grid::make(2)->schema([
                                            Select::make('semester_genap_start_month')->label('Semester Genap Dimulai')->options($months)->required(),
                                            Select::make('semester_genap_end_month')->label('Semester Genap Berakhir')->options($months)->required(),
                                        ]),
                                    ]),
                            ]),
                    ])
                    ->columnSpanFull(), // Pastikan tabs mengambil lebar penuh
            ])
            ->statePath('data');
    }

    public function saveAction(): Action
    {
        return Action::make('save')
            ->label('Simpan Pengaturan')
            ->submit('save');
    }

    public function save(): void
    {
        $data = $this->form->getState();

        foreach ($data as $key => $value) {
            if ($value !== null) { // Hanya simpan jika ada nilainya
                Setting::updateOrCreate(
                    ['key' => $key],
                    ['value' => $value]
                );
            }
        }

        Notification::make()
            ->title('Pengaturan berhasil disimpan')
            ->success()
            ->send();
    }

    public static function shouldRegisterNavigation(): bool
    {
        return Auth::check() && Auth::user()->role === 'Admin';
    }

    public static function canAccess(): bool
    {
        return Auth::check() && Auth::user()->role === 'Admin';
    }
}
