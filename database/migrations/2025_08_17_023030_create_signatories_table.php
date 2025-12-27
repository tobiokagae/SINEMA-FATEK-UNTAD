<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('signatories', function (Blueprint $table) {
            $table->id();
            // Setiap fakultas hanya punya satu penandatangan
            $table->foreignId('faculty_id')->unique()->constrained()->cascadeOnDelete();
            $table->string('name');
            $table->string('nip');
            $table->string('jabatan');
            $table->string('pangkat');
            $table->string('golongan');
            $table->string('signature_image_path')->nullable();
            $table->string('stamp_image_path')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('signatories');
    }
};
