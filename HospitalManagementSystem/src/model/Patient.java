package model;

import java.util.UUID;

public class Patient {
    private String id;
    private String name;
    private int age;
    private String gender;
    private String ward;
    private String admitDate;

    public Patient(String name, int age, String gender, String ward, String admitDate) {
        this.id = UUID.randomUUID().toString();
        this.name = name;
        this.age = age;
        this.gender = gender;
        this.ward = ward;
        this.admitDate = admitDate;
    }

    public String getId() { return id; }
    public String getName() { return name; }
  /*  public int getAge() { return age; }
    public String getGender() { return gender; }
    public String getWard() { return ward; }
    public String getAdmitDate() { return admitDate; }

    public void setWard(String ward) { this.ward = ward; } */
}
