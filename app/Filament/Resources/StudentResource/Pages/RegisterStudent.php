<?php

namespace App\Filament\Resources\StudentResource\Pages;

use App\Models\Faculty;
use App\Models\Student;
use App\Models\StudyProgram;
use App\Models\User;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Form;
use Filament\Forms\Get;
use Filament\Pages\Auth\Register as BaseRegister;
use Illuminate\Auth\Events\Registered;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules\Password;

class RegisterStudent extends BaseRegister
{
    /**
     * Definisikan formulir registrasi
     */
    public function form(Form $form): Form
    {
        return $form
            ->schema([
                // Field untuk tabel 'users'
                $this->getNameFormComponent(),
                $this->getEmailFormComponent(),
                $this->getPasswordFormComponent(),
                $this->getPasswordConfirmationFormComponent(),

                // Field tambahan untuk tabel 'students'
                TextInput::make('nim')
                    ->label('Nomor Induk Mahasiswa')
                    ->unique(table: 'students', column: 'nim')
                    ->maxLength(9) // batasi maksimal 9 karakter
                    ->afterStateUpdated(fn($state, callable $set) => $set('nim', strtoupper(substr($state, 0, 9))))
                    ->extraAttributes(['style' => 'text-transform: uppercase;'])
                    ->reactive()
                    ->required(),

                Select::make('faculty_id')
                    ->label('Fakultas')
                    ->options(Faculty::all()->pluck('name', 'id'))
                    ->live()
                    ->searchable()
                    ->required(),

                Select::make('study_program_id')
                    ->label('Program Studi')
                    ->options(function (Get $get) {
                        $facultyId = $get('faculty_id');
                        if (!$facultyId) {
                            return [];
                        }
                        return StudyProgram::where('faculty_id', $facultyId)->pluck('name', 'id');
                    })
                    ->searchable()
                    ->required(),
            ]);
    }

    /**
     * Override metode register untuk menyimpan data ke tabel User dan Student
     */
    protected function handleRegistration(array $data): Model
    {
        // 1. Buat record User
        $user = User::create([
            'name' => $data['name'],
            'email' => $data['email'],
            'password' => $data['password'],
            'role' => 'Student',
        ]);

        // 2. Buat record Student yang berelasi
        Student::create([
            'user_id' => $user->id,
            'nim' => $data['nim'],
            'faculty_id' => $data['faculty_id'],
            'study_program_id' => $data['study_program_id'],
        ]);

        // Gunakan event standar Laravel untuk memicu pengiriman email.
        // event(new Registered($user));

        return $user;
    }
}
