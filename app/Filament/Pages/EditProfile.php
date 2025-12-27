<?php

namespace App\Filament\Pages;

use Filament\Forms\Components\Section;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Form;
use Filament\Pages\Auth\EditProfile as BaseEditProfile;
use Illuminate\Support\Facades\Auth;

class EditProfile extends BaseEditProfile
{
    public function form(Form $form): Form
    {
        return $form
            ->schema([
                Section::make('Informasi Akun')
                    ->schema([
                        $this->getNameFormComponent(),
                        $this->getEmailFormComponent(),
                        $this->getPasswordFormComponent(),
                        $this->getPasswordConfirmationFormComponent(),
                    ]),

                // Section ini hanya akan muncul jika pengguna yang login adalah 'Student'
                Section::make('Informasi Akademik')
                    ->description('Informasi ini tidak dapat diubah melalui halaman ini.')
                    ->schema([
                        TextInput::make('nim')
                            ->label('NIM')
                            ->disabled()
                            ->dehydrated(false),
                        TextInput::make('faculty')
                            ->label('Fakultas')
                            ->disabled()
                            ->dehydrated(false),
                        TextInput::make('study_program')
                            ->label('Program Studi')
                            ->disabled()
                            ->dehydrated(false),
                    ])
                    ->visible(fn(): bool => Auth::user()->role === 'Student'),
            ]);
    }

    /**
     * Mengisi field informasi akademik saat halaman dimuat
     */
    protected function fillForm(): void
    {
        parent::fillForm(); // Jalankan fungsi bawaan terlebih dahulu

        $user = Auth::user();

        if ($user->role === 'Student' && $user->student) {
            $studentData = [
                'nim' => $user->student->nim,
                'faculty' => $user->student->faculty->name,
                'study_program' => $user->student->studyProgram->name,
            ];
            // Gabungkan data user dengan data student
            $this->form->fill(array_merge($this->form->getState(), $studentData));
        }
    }
}
