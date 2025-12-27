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
        Schema::create('activity_types', function (Blueprint $table) {
            $table->id();
            $table->foreignId('activity_field_id')->constrained()->cascadeOnDelete();
            $table->text('name');
            $table->string('level')->nullable(); // e.g., "Internasional"
            $table->string('achievement')->nullable(); // e.g., "Juara I", "Ketua"
            $table->integer('score')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('activity_types');
    }
};
